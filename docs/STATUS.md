# STATUS

**Current phase:** 1 — Foundation, Ingestion, Cleaning, Station Registry
**State:** in progress
**Next phase:** 2 — Spatial indexing + demand panel (do not start until the Phase 1
Definition of Done below is fully checked)

---

## Phase 1 — Definition of Done

_(updated as items are verified; see the running log for evidence)_

- [ ] Repo structure + configs exist, nothing hardcoded that should be configurable
- [ ] Data quality report generated and saved to `outputs/`
- [ ] Cleaning removes/flags issues with logged counts per rule (no silent drops)
- [ ] Timestamps correctly localized, DST verified around all four 2023-2024 transitions
- [ ] Station registry built, coordinate anomalies flagged
- [ ] 7-day dev sample exists and is used for the next phase's first pass
- [ ] `docs/STATUS.md` updated, phase committed to git

---

## Artifacts produced so far

| Artifact | Path | Notes |
|---|---|---|
| Typed raw trips | `data/raw/trips/month=YYYYMM/` | 79,410,195 rows, 2.5 GB, tz-aware UTC |
| Cleaned trips | `data/interim/trips_clean.parquet` | single file, sorted by `started_at` |
| Hourly weather | `data/external/weather_hourly.parquet` | 17,544 rows (731 days × 24 h) |
| Events | `data/external/events.parquet` | 557,762 rows / 75,741 distinct events |
| Event locations | `data/external/event_locations.parquet` | 19,012 strings needing geocoding |
| Station registry | `data/spatial/station_registry.parquet` | derived from trip activity |
| Dev sample | `data/dev_sample/` | 7 days, 2024-06-03 .. 2024-06-09 |
| Quality report | `outputs/reports/data_quality_report_*.md` / `.json` | raw profile + cleaning waterfall |
| Ingest manifest | `outputs/reports/ingest_manifest.json` | per-CSV row counts and timings |

---

## Key decisions made in Phase 1

**Timestamps are stored as tz-aware UTC, not naive local.** Citi Bike publishes naive
`America/New_York` wall-clock time. Binning naive local time merges the two passes
through the repeated fall-back hour into one bin and leaves a phantom gap. Storing
UTC keeps the 15-minute grid dense and unambiguous; local calendar features are
derived by converting back (`src/data/timezone.to_local`).

**DST distortion is enumerated, not hidden.** With `ambiguous="earliest"`, the second
pass through the repeated local hour is unreachable from a naive timestamp: that UTC
hour is empty by construction and the first pass is over-filled. Four hours across
2023-2024 are affected. `src/data/timezone.dst_unreliable_utc_hours()` lists them, the
quality report shows the counts, and Phase 2 must flag those bins rather than model
them as observed demand. Spring-forward timestamps (which cannot exist) are shifted
forward one hour and counted.

**Station ids are strings, never floats.** Citi Bike ids look like `5137.10`; parsing
them as numbers silently collapses them onto `5137.1` and merges distinct stations.

**The station registry is derived from trip activity, not the roster CSV.** The roster
is a snapshot of whatever date it was pulled and cannot describe which stations existed
during 2023-2024. It is loaded only as a cross-check and reported, never substituted.

**A single, globally time-sorted clean file.** `data/interim/trips_clean.parquet` is
sorted by `started_at` end to end, and sortedness is asserted two independent ways
(Parquet row-group statistics + a full pairwise scan of the column in file order).
Everything downstream — panel building, lag features, chronological splits — depends
on that ordering, so it is verified, not assumed.

---

## Known data problems (carried forward)

1. **Traffic data is unusable as downloaded.** `DOT_traffic_speeds_after_2018-07-01_20260824.csv`
   holds 194,130 rows spanning **2018-07-26 .. 2018-07-30** only — the Socrata UI export
   was row-capped rather than date-filtered. Zero overlap with 2023-2024.
   `sources.traffic_usable: false` in `configs/base.yaml` guards against building
   features from it. Ablation family **F (traffic)** is blocked until it is re-pulled
   via the Socrata API with a date filter and server-side aggregation
   (see `docs/DATA_SOURCES.md`).
2. **Events have no coordinates.** The export gives a free-text street description plus
   borough / community board / precinct. 19,012 distinct location strings need
   geocoding before events can be mapped to H3 cells — a Phase 4 task, sized here.
3. **No station capacity data.** As planned, Phase 8 estimates capacity statistically.
4. **`visibility` is not available** from the Open-Meteo archive (returned 100 % null);
   removed from the requested variable list.

---

## Running log

- **2026-08-24** — Phase 1 started. Repo scaffolded; configs written; ingest of all 90
  Citi Bike CSVs completed (79,410,195 rows → 2.5 GB Parquet in 2.0 min via Polars);
  weather and events pulled; cleaning rules, quality report, global chronological sort
  and the Phase 1 test suite implemented; dev sample verified end to end before the
  full run, per CLAUDE.md rule 5.
