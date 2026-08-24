# GeoPulse — NYC Citi Bike Demand Forecasting & Rebalancing

Short-horizon (15/30/45/60-minute) demand forecasting for the NYC Citi Bike network
at a **spatial-cell** granularity, and the operational layer that turns those
forecasts into rebalancing decisions.

The project answers four research questions:

1. Which **H3 resolution** (8 / 9 / 10) forecasts NYC bike demand best?
2. Does **H3 or S2** work better at matched granularity?
3. Do **TFT** and a **spatio-temporal GNN** beat a tuned **LightGBM**?
4. Do better forecasts actually produce better **rebalancing** outcomes?

## Data

Jan 1 2023 – Dec 31 2024. Citi Bike trip history (90 CSVs, ~15 GB, 79.4 M rides),
Open-Meteo hourly weather, NYC permitted events, NYC DOT traffic speeds.
See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) — including what is deferred and
what is currently broken.

## Layout

```
configs/     all tunable values (base + h3/s2/lightgbm/tft/stgnn overlays)
data/        raw/ interim/ processed/ spatial/ external/ dev_sample/   (gitignored)
src/         pipeline code: data, spatial, features, models, evaluation,
             inventory, rebalancing, utils
scripts/     runnable stages, numbered in execution order
tests/       leakage, data-validation and unit tests
outputs/     models, metrics, figures, experiments, reports
docs/        phase specs, data sources, STATUS
```

## Running Phase 1

```bash
make phase1          # ingest -> clean -> weather -> events -> registry -> dev sample
make test            # pytest
```

Or stage by stage:

```bash
python scripts/01_ingest.py            # raw CSV  -> typed UTC Parquet   (data/raw/trips)
python scripts/02_clean.py             # quality report + rules + sort   (data/interim)
python scripts/03_fetch_weather.py     # Open-Meteo archive              (data/external)
python scripts/04_prepare_events.py    # NYC permitted events            (data/external)
python scripts/05_station_registry.py  # station registry                (data/spatial)
python scripts/06_dev_sample.py        # 7-day dev slice                 (data/dev_sample)
```

Every stage takes `--dev-sample` or is derived from the dev sample, so a new
pipeline step can be verified on 7 days before it touches two years.

## Ground rules

- **Phase-gated.** Finish a phase's Definition of Done before starting the next.
- **No leakage.** Every feature must be computable at `forecast_time`.
- **Chronological splits.** Train Jan 2023–Aug 2024 · Validate Sep–Oct 2024 ·
  Test Nov–Dec 2024, opened once, in Phase 7.
- **Config-driven.** Thresholds live in `configs/`, never inline.
- **No silent drops.** Every removed row is attributed to a named, counted rule.

Current progress: [`docs/STATUS.md`](docs/STATUS.md).
