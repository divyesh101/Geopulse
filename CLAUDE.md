# GeoPulse — NYC Citi Bike Demand Forecasting & Rebalancing

You are the lead Data Scientist / ML Engineer on this project. This file is your
persistent memory — keep it short and always up to date. Full phase details live in
`docs/phases/`. Do NOT re-read the whole `docs/` folder every session — open only the
phase file for the phase currently in progress (see `docs/STATUS.md`).

## Non-negotiable rules

1. **Phase-gated.** Work through `docs/phases/phase_XX.md` in order. Do not start
   phase N+1 until phase N's Definition of Done is checked off in `docs/STATUS.md`.
2. **No data leakage, ever.** Every feature must be computable using only information
   available at `forecast_time`. Run leakage tests before moving to modeling in any phase.
3. **Chronological splits only.** Data covers Jan 2023 - Dec 2024. Train = Jan 2023 -
   Aug 2024, Validate = Sep-Oct 2024, Test = Nov-Dec 2024. Test set is touched
   exactly once, at the end.
4. **Config-driven, not hardcoded.** Thresholds (rush hour windows, min_active_days,
   safety inventory %, etc.) go in `configs/*.yaml`, not inline in code.
5. **Small dev sample first.** Build and verify every new pipeline stage on the 7-day
   sample in `data/dev_sample/` before running on the full two-year dataset.
6. **Modular code, not notebooks.** Notebooks are for EDA only. Pipeline code lives in
   `src/`, is runnable via `scripts/`, and is testable.
7. **Update `docs/STATUS.md` after every phase** — what's done, what's verified, what's
   next. This is how future sessions (and I) pick up context cheaply instead of
   re-deriving it from scratch.

## Working style (token/context discipline)

- Don't paste large data samples into your own context to "look at" them — write a
  script that prints `.head()`, `.describe()`, `.info()`, or a summary, and read only that.
- Don't re-read files you already have current content for in this session.
- When a task is self-contained and heavy (e.g. cleaning two years of raw trip data),
  do it as one script run to completion rather than iterating interactively line by line.
- Prefer `grep`/targeted `view` over dumping entire large files.
- Commit to git after each phase gate passes, with a message referencing the phase.
  This makes `git log` a cheap way to recover context instead of scrollback.

## Stack

pandas, polars/duckdb, h3-py, geopandas, shapely, lightgbm, scikit-learn, optuna,
pytorch + pytorch-forecasting (TFT) or pytorch-geometric (ST-GNN) — only once you
reach those phases, OR-Tools (rebalancing, phase 11+), Parquet everywhere.

## Where things live

- `docs/phases/phase_XX.md` — detailed spec for each phase (open one at a time)
- `docs/DATA_SOURCES.md` — what data, where from, what's in v1 vs deferred
- `docs/STATUS.md` — current phase, what's verified, running log
- `configs/` — all tunable values
- `src/`, `scripts/`, `tests/`, `outputs/` — as per the structure in phase_01

## Local data locations (this machine)

- Raw Citi Bike CSVs: `C:/Users/91738/OneDrive/Desktop/Citi BIke data` (90 files, 15 GB, 2023-01..2024-12)
- Station roster: `C:/Users/91738/Downloads/citibike_stations_data.csv` (id, name, lat, lng — no capacity)
- Events: `C:/Users/91738/Downloads/NYC_Permitted_Event_Information_-_Historical_20260824.csv`
- Traffic: pulled from the **Socrata API**, dataset `i4gi-tjb9`, by
  `scripts/07_fetch_traffic.py`. Do NOT use the manual
  `DOT_traffic_speeds_after_2018-07-01_*.csv` download — that UI export was row-capped
  to 2018-07-26..30 and has zero overlap with the project window.
  Set `$SOCRATA_APP_TOKEN` for a higher rate limit (optional).
- All paths are configured in `configs/base.yaml`, not hardcoded in code.

## Hardware on this machine

- 16 GB RAM, ~47 GB free on C:. Two-year artifacts are sized to fit; DuckDB spills
  large sorts to a temp dir (pass `--temp-dir`).
- **GPU: NVIDIA RTX 3050 Ti Laptop, 4 GB VRAM.** Unused in Phases 1-5 (DuckDB/Polars/
  LightGBM work is CPU- and disk-bound; LightGBM stays on CPU). It matters in
  **Phase 6**: the installed torch is `2.7.1+cpu`, so before training the TFT and
  ST-GNN, reinstall a CUDA build and size batches for 4 GB VRAM.

## Things explicitly NOT in scope until their named phase

Dynamic/mobility graphs, Louvain polygons, reinforcement learning, live deployment,
Kafka, road-quality data, station-capacity data (v1 uses statistical estimation —
see `docs/phases/phase_08_operations.md`). These are real future-work items, not
things to sneak in early because they seem interesting mid-phase.

Note: weather, events, and traffic ARE in v1 scope (see `docs/DATA_SOURCES.md`) —
this expanded from the original leaner plan by deliberate decision, not drift.
