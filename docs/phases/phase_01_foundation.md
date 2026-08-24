# Phase 1 - Foundation, Ingestion, Cleaning, Station Registry

## Goal
A trustworthy, reproducible raw-to-clean pipeline for Citi Bike trips + NOAA weather,
with a documented data-quality report. No modeling yet.

## Repo structure
```
geopulse/
|-- configs/{base,h3,s2,lightgbm,tft,stgnn}.yaml
|-- data/{raw,interim,spatial,processed,external,dev_sample}/
|-- src/{data,spatial,features,models,evaluation,inventory,rebalancing,utils}/
|-- scripts/  (01_ingest.py, 02_clean.py, ...)
|-- tests/
|-- outputs/{models,metrics,figures,experiments}/
|-- notebooks/eda.ipynb
|-- requirements.txt / README.md / Makefile
```

## Tasks
1. Scaffold repo + configs (empty/defaults, no magic numbers in code).
2. Ingest Citi Bike trips, Jan 1 2023 - Dec 31 2024, plus hourly weather, NYC
   permitted events, and NYC DOT traffic speeds for the same period.
   See `docs/DATA_SOURCES.md` for exact sources.
3. Data quality report (row counts, missing coords/stations, duplicate ride_ids,
   invalid timestamps, `ended_at <= started_at`, duration distribution, coordinate
   ranges, rides/day, rides/month). Never silently drop rows - log every removal rule
   and count.
4. Clean trips: keep ride_id, rideable_type, started_at, ended_at, start/end
   station_id + name + lat/lng, member_casual. Derive `ride_duration`.
5. Timezone: treat Citi Bike + weather timestamps as `America/New_York`, handle
   all four DST transitions correctly (spring/fall 2023 and 2024) - do not treat
   timestamps as naive strings.
6. Build station registry: station_id, name, median lat/lng (representative coords),
   first_seen, last_seen, ride count. Flag stations whose coords jump unrealistically.
7. Build a **7-day dev sample** (`data/dev_sample/`) - every later pipeline stage gets
   verified here first, before running on the full two years.

## Definition of Done
- [ ] Repo structure + configs exist, nothing hardcoded that should be configurable
- [ ] Data quality report generated and saved to `outputs/`
- [ ] Cleaning removes/flags issues with logged counts per rule (no silent drops)
- [ ] Timestamps correctly localized, DST verified around all four transitions in 2023-2024
- [ ] Station registry built, coordinate anomalies flagged
- [ ] 7-day dev sample exists and is used for the next phase's first pass
- [ ] `docs/STATUS.md` updated, phase committed to git
