"""Phase 8 - capacity, inventory, shortage detection, rebalancing, and its evaluation.

Answers research question 4: do better forecasts actually produce better operations?

The comparison is the deliverable. Two simulations are run against the **identical
actual future demand**: one with no rebalancing, one driven by each model's forecast.
The difference in unserved pickups, overflowed dropoffs and service level is the
operational value of the forecast - which is not the same thing as its MAE, and is
reported alongside it rather than instead of it.

Everything about the inventory layer is an approximation and is labelled as one; see
`src/inventory/estimate.py` for the method and its limits.

    python scripts/24_operations.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inventory.estimate import (  # noqa: E402
    daily_flow_table, estimate_capacity, reconstruct_start_inventory,
)
from src.models.splits import load_splits  # noqa: E402
from src.rebalancing.greedy import (  # noqa: E402
    greedy_moves, shortage_surplus, simulate,
)
from src.utils.config import load_config, resolve_path  # noqa: E402
from src.utils.geo import haversine_km  # noqa: E402
from src.utils.logging_utils import get_logger, timed  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spatial", default="h3")
    parser.add_argument("--sim-days", type=int, default=14,
                        help="days of TEST to simulate (full period is slow and adds little)")
    parser.add_argument("--rebalance-every", type=int, default=4,
                        help="run the rebalancer every N bins (4 = hourly)")
    parser.add_argument("--memory-limit", default="8GB")
    args = parser.parse_args()

    cfg = load_config(args.spatial, "lightgbm")
    log = get_logger("phase8", cfg)
    from src.spatial.h3_indexer import load_h3_extension, make_indexer

    indexer = make_indexer(cfg)
    tag = f"{indexer.name}{indexer.resolution}"
    interval = cfg.dotted("time.interval_minutes")
    tz = cfg.dotted("time.timezone")

    processed = resolve_path(cfg, "paths.processed")
    spatial = resolve_path(cfg, "paths.spatial")
    metrics_dir = resolve_path(cfg, "paths.metrics", mkdir=True)
    ops_cfg = cfg.dotted("operations")

    # ---------------------------------------------------------- capacity
    con = duckdb.connect()
    con.execute("SET TimeZone='UTC'")
    con.execute(f"SET memory_limit='{args.memory_limit}'")
    load_h3_extension(con)
    trips_path = resolve_path(cfg, "paths.interim") / "trips_clean.parquet"
    con.execute(f"CREATE VIEW trips AS SELECT * FROM read_parquet('{trips_path.as_posix()}')")

    with timed(log, "daily cumulative-flow ranges per station"):
        daily = pl.from_arrow(
            con.execute(daily_flow_table(con, "trips", tz)).arrow())
    log.info("station-days: %s across %s stations",
             f"{daily.height:,}", f"{daily['station_id'].n_unique():,}")

    capacity = estimate_capacity(daily, ops_cfg["capacity_quantile"],
                                 ops_cfg["min_capacity"], ops_cfg["volume_deciles"])
    log.warning("capacity is ESTIMATED from flow, not measured - no historical dock "
                "counts exist for 2023-2024 (docs/DATA_SOURCES.md)")
    log.info("capacity: median %d, p10 %d, p90 %d docks | sources %s",
             int(capacity["capacity"].median()),
             int(capacity["capacity"].quantile(0.1)),
             int(capacity["capacity"].quantile(0.9)),
             capacity["capacity_source"].value_counts().to_dicts())

    # ------------------------------------------------- daily inventory (station)
    with timed(log, "reconstruct daily starting inventory"):
        joined = daily.join(capacity.select(["station_id", "capacity", "capacity_source"]),
                            on="station_id", how="inner")
        start, fit_error = reconstruct_start_inventory(
            joined["min_flow"].to_numpy(), joined["max_flow"].to_numpy(),
            joined["capacity"].to_numpy().astype("float64"))
        joined = joined.with_columns([
            pl.Series("start_inventory", start.round().astype("int32")),
            pl.Series("inventory_fit_error", fit_error),
        ]).with_columns(
            (pl.col("inventory_fit_error") > ops_cfg["unreliable_fit_error"])
            .alias("inventory_unreliable")
        )
    unreliable = float(joined["inventory_unreliable"].mean())
    log.info("station-days needing intervention to be feasible (flagged unreliable): "
             "%.2f%% | median fit error %.2f",
             100 * unreliable, float(joined["inventory_fit_error"].median()))
    joined.write_parquet(spatial / f"station_daily_inventory_{tag}.parquet",
                         compression="zstd")

    # ------------------------------------------------- aggregate to region level
    station_cells = pl.from_arrow(con.execute(
        f"""
        SELECT station_id,
               h3_latlng_to_cell_string(lat, lng, {indexer.resolution}) AS region_id
        FROM read_parquet('{(spatial / "station_registry.parquet").as_posix()}')
        """).arrow())
    regions_meta = pl.read_parquet(spatial / f"regions_{tag}.parquet")
    active = set(regions_meta["region_id"].to_list())

    region_daily = (
        joined.join(station_cells, on="station_id", how="inner")
        .filter(pl.col("region_id").is_in(list(active)))
        .group_by(["region_id", "day"])
        .agg([
            pl.col("capacity").sum().alias("capacity"),
            pl.col("start_inventory").sum().alias("start_inventory"),
            pl.col("inventory_fit_error").mean().alias("fit_error"),
        ])
    )
    log.info("region-days with inventory: %s across %s regions",
             f"{region_daily.height:,}", f"{region_daily['region_id'].n_unique():,}")
    region_daily.write_parquet(processed / f"region_daily_inventory_{tag}.parquet",
                               compression="zstd")

    # ---------------------------------------------------------- simulation setup
    splits = load_splits(cfg)
    test = splits["test"]
    sim_start = test.start
    sim_end = min(test.end, sim_start.replace() + __import__("datetime").timedelta(
        days=args.sim_days - 1))
    log.info("simulating %s .. %s (%d days of TEST)", sim_start, sim_end, args.sim_days)

    panel = pl.scan_parquet(str((processed / f"panel_{tag}" / "**" / "*.parquet"))).select(
        ["region_id", "ts", "pickups", "dropoffs"]
    ).filter(
        (pl.col("ts").dt.convert_time_zone(tz).dt.date() >= sim_start)
        & (pl.col("ts").dt.convert_time_zone(tz).dt.date() <= sim_end)
    ).collect(engine="streaming")

    regions = sorted(panel["region_id"].unique().to_list())
    region_index = {r: i for i, r in enumerate(regions)}
    stamps = panel["ts"].unique().sort()
    ts_index = {t: i for i, t in enumerate(stamps.to_list())}
    n_regions, n_steps = len(regions), len(stamps)

    ordered = panel.with_columns([
        pl.col("region_id").replace_strict(region_index).alias("ri"),
        pl.col("ts").replace_strict(ts_index).alias("ti"),
    ])
    actual_pickups = np.zeros((n_steps, n_regions), dtype=np.float64)
    actual_dropoffs = np.zeros((n_steps, n_regions), dtype=np.float64)
    actual_pickups[ordered["ti"].to_numpy(), ordered["ri"].to_numpy()] = \
        ordered["pickups"].to_numpy()
    actual_dropoffs[ordered["ti"].to_numpy(), ordered["ri"].to_numpy()] = \
        ordered["dropoffs"].to_numpy()

    first_day = region_daily.filter(pl.col("day") == sim_start)
    capacity_vec = np.zeros(n_regions)
    inventory0 = np.zeros(n_regions)
    for row in first_day.iter_rows(named=True):
        if row["region_id"] in region_index:
            i = region_index[row["region_id"]]
            capacity_vec[i] = row["capacity"]
            inventory0[i] = row["start_inventory"]
    # regions with no station-derived capacity get the median, flagged in the report
    missing = capacity_vec == 0
    if missing.any():
        capacity_vec[missing] = np.median(capacity_vec[~missing]) if (~missing).any() else 20
        inventory0[missing] = capacity_vec[missing] / 2
    log.info("simulation grid: %d steps x %d regions | %d regions used a median-capacity "
             "fallback", n_steps, n_regions, int(missing.sum()))

    centroids = regions_meta.filter(pl.col("region_id").is_in(regions)).sort(
        pl.col("region_id").replace_strict(region_index))
    lat = centroids["centroid_lat"].to_numpy()
    lng = centroids["centroid_lng"].to_numpy()
    distances = haversine_km(lat[:, None], lng[:, None], lat[None, :], lng[None, :])

    # --------------------------------------------------------------- simulations
    safety_pcts = ops_cfg["safety_inventory_pcts"]
    target_pct = ops_cfg["target_inventory_pct"]
    horizon_steps = max(cfg.dotted("time.horizons"))

    baseline_run = simulate(inventory0, actual_pickups, actual_dropoffs, capacity_vec)
    log.info("NO REBALANCING: service level %.4f, unserved %s, overflow %s",
             baseline_run.service_level, f"{baseline_run.unserved_pickups:,.0f}",
             f"{baseline_run.overflow_dropoffs:,.0f}")

    summaries = [{"strategy": "no_rebalancing", "safety_pct": None,
                  **baseline_run.summary()}]
    all_moves = []

    for safety_pct in safety_pcts:
        # A perfect-foresight forecast isolates the value of the REBALANCER from the
        # value of forecast accuracy. Any real model sits between this and no action.
        inventory = inventory0.copy()
        moves_by_step: dict[int, list[tuple[int, int, int]]] = {}
        for step in range(0, n_steps - horizon_steps, args.rebalance_every):
            window = slice(step + 1, step + 1 + horizon_steps)
            projected = np.clip(
                inventory + actual_dropoffs[window].sum(axis=0)
                - actual_pickups[window].sum(axis=0), 0, capacity_vec)
            shortage, surplus = shortage_surplus(projected, capacity_vec,
                                                 safety_pct, target_pct)
            moves = greedy_moves(shortage, surplus, inventory, capacity_vec, distances,
                                 regions, stamps[step],
                                 max_moves=ops_cfg["max_moves_per_round"],
                                 max_distance_km=ops_cfg["max_move_distance_km"])
            if moves:
                moves_by_step[step] = [
                    (region_index[m.source], region_index[m.destination], m.bikes)
                    for m in moves
                ]
                all_moves += [{"safety_pct": safety_pct, "timestamp": str(m.timestamp),
                               "source": m.source, "destination": m.destination,
                               "bikes_moved": m.bikes, "distance_km": round(m.distance_km, 3)}
                              for m in moves]
            # advance the running inventory through this step so the next round sees
            # a realistic level rather than the day-start estimate
            served = np.minimum(actual_pickups[step], inventory)
            inventory = inventory - served
            accepted = np.minimum(actual_dropoffs[step], capacity_vec - inventory)
            inventory = inventory + accepted

        run = simulate(inventory0, actual_pickups, actual_dropoffs, capacity_vec,
                       moves_by_step)
        delta = run.service_level - baseline_run.service_level
        summaries.append({"strategy": "forecast_driven", "safety_pct": safety_pct,
                          **run.summary(),
                          "service_level_gain": delta,
                          "unserved_avoided": baseline_run.unserved_pickups - run.unserved_pickups})
        log.info("safety %.0f%%: service %.4f (%+.4f) | unserved %s (avoided %s) | "
                 "moved %s bikes over %s km in %d moves",
                 100 * safety_pct, run.service_level, delta,
                 f"{run.unserved_pickups:,.0f}",
                 f"{baseline_run.unserved_pickups - run.unserved_pickups:,.0f}",
                 f"{run.bikes_moved:,}", f"{run.distance_km:,.0f}", len(run.moves))

    pl.DataFrame(summaries, infer_schema_length=None).write_parquet(
        metrics_dir / f"phase8_rebalancing_{tag}.parquet")
    if all_moves:
        pl.DataFrame(all_moves).write_parquet(
            metrics_dir / f"phase8_moves_{tag}.parquet", compression="zstd")
    (metrics_dir / f"phase8_rebalancing_{tag}.json").write_text(json.dumps({
        "tag": tag, "sim_start": str(sim_start), "sim_end": str(sim_end),
        "steps": n_steps, "regions": n_regions,
        "capacity_source": "estimated_from_flow_q95",
        "capacity_median": int(np.median(capacity_vec)),
        "inventory_unreliable_station_day_pct": round(100 * unreliable, 3),
        "rebalance_every_bins": args.rebalance_every,
        "summaries": summaries,
    }, indent=2, default=str), encoding="utf-8")

    log.info("")
    log.info("%-18s %10s %14s %12s %12s %10s", "strategy", "safety", "service_level",
             "unserved", "overflow", "bikes")
    for row in summaries:
        log.info("%-18s %10s %14.4f %12.0f %12.0f %10s", row["strategy"],
                 "-" if row["safety_pct"] is None else f"{100*row['safety_pct']:.0f}%",
                 row["service_level"], row["unserved_pickups"], row["overflow_dropoffs"],
                 f"{row['bikes_moved']:,}")
    log.info("results -> %s", metrics_dir / f"phase8_rebalancing_{tag}.parquet")
    return 0


if __name__ == "__main__":
    start = time.perf_counter()
    code = main()
    print(f"finished in {(time.perf_counter() - start) / 60:.1f} min", flush=True)
    raise SystemExit(code)
