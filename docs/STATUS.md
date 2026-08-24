# STATUS

**Current phase:** 2 — Spatial indexing + demand panel — **COMPLETE**
**State:** Phase 1 gate 11/11 (`scripts/09_phase1_check.py`),
Phase 2 gate 11/11 (`scripts/11_phase2_check.py`), 100 tests passing
**Next phase:** 3 — Minimal baseline (STOP-AND-VERIFY GATE). Seasonal Naive +
a simple LightGBM per (target, horizon), plus the leakage and data-validation
test suites. Nothing from Phase 4 starts until Phase 3 is boring and correct.

---

## Phase 2 — Definition of Done

Verified by `scripts/11_phase2_check.py` against the built panel.

- [x] `SpatialIndexer` interface + `H3Indexer` implemented and unit-tested
- [x] Active-region selection implemented, counts reported
- [x] Dense panel: exactly one row per active region per interval, no gaps
- [x] Targets h1-h4 implemented and shift-tested against an independent join
- [x] Verified on the 7-day dev sample first, then the full range
- [x] `docs/STATUS.md` updated, phase committed to git

### The panel

| | |
|---|---|
| Path | `data/processed/panel_h39/month=YYYYMM/` (24 partitions, 277 MB) |
| Rows | **104,071,008** = 1,483 active regions x 70,176 bins — exactly dense |
| Grid | 2023-01-01 05:00 UTC .. 2025-01-01 04:45 UTC, 15-min bins, 0 irregular gaps |
| Columns | `region_id, ts, pickups, dropoffs, net_flow, dst_unreliable, pickup_h1..h4, dropoff_h1..h4` |
| Reconciliation | panel pickups 79,150,890 == trips in active regions inside the grid |
| Sparsity | 71.37% of (region, bin) cells have zero pickups at H3-9 |
| Sort order | `(region_id, ts)` within each month partition |

### Phase 2 decisions

**Active regions come from observed activity**: >= 500 trips AND >= 180 active days
over the two years. 1,570 regions were touched, 1,483 qualify, and they carry
**99.98% of all trip endpoints** — so the rule discards 87 marginal regions while
losing almost no demand.

**Indexing 79M trips took 0.8 s, not an hour.** Citi Bike snaps coordinates to
stations, so the whole dataset contains only **3,230 distinct (lat, lng) pairs**.
Those are indexed once into a lookup table and joined, instead of calling H3
158M times. It is exact, not an approximation, and `tests/test_spatial.py` asserts
the DuckDB and Python H3 paths agree on real NYC points at resolutions 8/9/10.

**Density is the contract.** A region with no trips in a bin is 0, not a missing
row. The grid is built as an explicit cross join and counts are joined onto it, so
`LEAD`-based targets and every later lag/rolling feature are computed on a
guaranteed gap-free series.

**Targets are shift-tested, not assumed.** `pickup_h{h}[r,t]` is re-derived by an
independent timestamp self-join at every horizon — in the unit tests on the dev
panel, and in the gate on 60 sampled regions (4.2M rows) of the full panel.
Horizon overrun is **NULL, never 0**: a zero would teach the model a phantom
demand collapse at the end of the series. Verified as exactly `regions x h` nulls.

**DST-distorted bins are flagged, carrying Phase 1's finding forward.** 24 bins
(6 distorted UTC hours x 4 bins) x 1,483 regions = 35,592 rows marked
`dst_unreliable`. Phase 3 must exclude or down-weight them rather than learn the
artificial nightly collapse they encode.

**Thresholds scale to the window.** `min_active_days: 180` is unreachable in a
7-day dev sample, which would have made the dev run select nothing and prove
nothing. `scaled_thresholds()` rescales by window length (dev: >= 5 trips /
>= 2 days) and logs loudly that it did, so the dev sample stays a real smoke test
of the same code path.

---

## Phase 1 — Definition of Done (complete)

---

Verified by `scripts/09_phase1_check.py`, which reads the produced artifacts rather
than taking anything on trust.

- [x] Repo structure + configs exist, nothing hardcoded that should be configurable
- [x] Data quality report generated and saved to `outputs/reports/`
- [x] Cleaning removes/flags issues with logged counts per rule (no silent drops)
- [x] Timestamps correctly localized, DST verified around all four 2023-2024 transitions
- [x] Station registry built, coordinate anomalies flagged
- [x] 7-day dev sample exists and is used for the next phase's first pass
- [x] `docs/STATUS.md` updated, phase committed to git

---

## Artifacts

| Artifact | Path | Notes |
|---|---|---|
| Typed raw trips | `data/raw/trips/month=YYYYMM/` | 79,410,195 rows, 2.5 GB, tz-aware UTC |
| **Cleaned trips** | `data/interim/trips_clean.parquet` | **79,165,067 rows, 2.42 GB, globally sorted by `started_at`** |
| Hourly weather | `data/external/weather_hourly.parquet` | 17,544 rows = 731 days x 24 h, no gaps |
| Events | `data/external/events.parquet` | 557,674 rows / 75,729 distinct events |
| Event locations | `data/external/event_locations.parquet` | 19,011 strings needing geocoding (Phase 4) |
| Raw traffic | `data/raw/traffic/month=YYYYMM/` | Socrata `i4gi-tjb9`, 23,758,184 observations, 82 MB |
| Cleaned traffic | `data/interim/traffic_clean.parquet` | 17,904,366 rows, 55 MB, sorted by `data_as_of` |
| Traffic links | `data/spatial/traffic_links.parquet` | 128 links + geometry, midpoints derived |
| Link/station proximity | `data/spatial/traffic_link_station_proximity.parquet` | distance from each link to nearest station |
| Station registry | `data/spatial/station_registry.parquet` | 2,459 stations from trip activity |
| Dev sample | `data/dev_sample/` | 7 days, 2024-06-03 .. 2024-06-09, all sources |
| Quality reports | `outputs/reports/*.md` / `.json` | trips + traffic, raw profile and waterfalls |
| Manifests | `outputs/reports/*_manifest.json` | per-CSV and per-day row counts and timings |

---

## Cleaning waterfall (trips, full two years)

Every removal is attributed to the **first** rule the row violates, so the counts sum
exactly to the rows removed. Raw = 79,410,195.

| rule | rows removed | % of raw |
|---|---|---|
| duplicate_ride_id | 0 | 0 |
| null_ride_id | 0 | 0 |
| null_timestamp | 0 | 0 |
| outside_project_window | 276 | 0.0003% |
| end_before_start | 643 | 0.0008% |
| duration_too_short | 182 | 0.0002% |
| duration_too_long | 37,627 | 0.047% |
| missing_coords | 206,222 | 0.260% |
| coords_out_of_bbox | 178 | 0.0002% |
| **TOTAL REMOVED** | **245,128** | **0.309%** |
| **KEPT** | **79,165,067** | **99.691%** |

Not a single duplicate `ride_id` in 79.4M rows across two years — worth knowing, and
the de-duplication step is still in place so a future month cannot slip one past.

---

## Key decisions made in Phase 1

**Timestamps are stored as tz-aware UTC, not naive local.** Citi Bike publishes naive
`America/New_York` wall-clock time. Binning naive local time merges the two passes
through the repeated fall-back hour into one bin and leaves a phantom gap. Storing
UTC keeps the 15-minute grid dense and unambiguous; local calendar features are
derived by converting back (`src/data/timezone.to_local`).

**DST distortion is enumerated, not hidden.** With `ambiguous="earliest"` the second
pass through the repeated local hour is unreachable from a naive timestamp. Measured
in the data: `2023-11-05 05:00 UTC` holds 2,921 rides (both passes) while
`06:00 UTC` holds 0; same shape on `2024-11-03` (3,534 / 0). Spring-forward
timestamps that cannot exist are shifted forward one hour (617 and 582 rides).
`src/data/timezone.dst_unreliable_utc_hours()` lists the four affected hours, the
quality report tabulates them, and a test asserts the behaviour.
**Phase 2 must flag those bins rather than model them as observed demand.**

**Station ids are strings, never floats.** Citi Bike ids look like `5137.10`; parsing
them as numbers collapses that onto `5137.1` and merges distinct stations.

**The station registry is derived from trip activity, not the roster CSV.** Confirmed
by the cross-check: 2,204 of 2,459 observed stations appear in the roster, so **255
stations that really operated in 2023-2024 are missing from the roster snapshot**.
Where both exist, coordinates agree to under 10 cm. 9 stations were flagged for
coordinate anomalies and 75 were renamed during the period.

**A single, globally time-sorted clean file.** `data/interim/trips_clean.parquet` is
sorted by `started_at` end to end, asserted two independent ways (Parquet row-group
statistics + a full pairwise scan of the column in file order): 0 violations,
0 inversions across 79,165,067 rows.

**How that sort is produced matters.** A single global `ORDER BY` over 79M wide rows
spilled 8 GB and had not finished after an hour. Because the raw data is already
partitioned by the local month of `started_at`, sorting each month (~3M rows, in
memory) and concatenating the parts in month order yields the identical global
ordering — 90 seconds of sorting plus a streaming concatenation. The verifier proves
the result rather than trusting the argument.

**Traffic is pulled from the Socrata API, not the UI export**, requesting only the
columns that vary per observation. Geometry (`link_points`, `encoded_poly_line`) is
static per link and lives in the link registry; repeating it per row is what made the
manual export unusable. Pagination is by time window, not `$offset`, so the pull is
indexed and resumable.

---

## Bugs found and fixed during Phase 1

**Silent-drop bug in de-duplication (both cleaners).** `WHERE key NOT IN (SELECT ...)`
evaluates to NULL — not TRUE — when the probed key is NULL, so any row with a NULL
key was filtered out with **no rule attributed** — precisely the unattributed drop
this phase forbids. Found by a traffic test whose waterfall failed to reconcile
(7 + 3 ≠ 12). Null-key rows now bypass de-duplication and are caught by named
`null_ride_id` / `null_link_id` / `null_timestamp` rules. Latent in the trips path
too; it only escaped notice because `ride_id` had zero nulls.

**DST profile bucketed in local time.** `date_trunc('hour', started_at)` truncates in
the DuckDB *session* timezone, which for `America/New_York` folds both passes of the
repeated hour onto one label and shifted the reported counts by an hour — making the
report contradict the (correct) pipeline. Now bucketed via `AT TIME ZONE 'UTC'`.

**`verify_sorted` was materialising 79M Python datetimes**, turning a check into a
multi-minute stall. Switched to a numpy comparison: 2.8 s for the full file, and the
whole test suite went from 403 s to 12 s.

**`.gitignore` `data/` also excluded `src/data/`** — the pipeline package — because a
bare directory pattern matches at any depth. Now `/data/`.

---

## Known data problems (carried forward)

0. **Traffic completeness is provable.** The pull returned 23,758,184 rows, exactly
   matching the server-side `count(1)` for the same window taken before the fetch
   began. Cleaning kept 17,904,366 (75.36%).
1. **Traffic coverage is thin where it matters.** The feed covers arterials, highways
   and bridges: only **46 of 128 links sit within 500 m of any Citi Bike station**,
   and all 27 Staten Island links are irrelevant (no Citi Bike service). Manhattan is
   well covered (25 of 26 links within 500 m), Queens barely (9 of 39). Traffic
   features will be dense in Manhattan and sparse elsewhere. See
   `data/spatial/traffic_link_station_proximity.parquet` and `docs/DATA_SOURCES.md`.
   A null result for ablation family F would be a legitimate finding, not a bug.
2. **The traffic feed has real multi-day outages — 45 days with zero readings**
   (e.g. 2023-01-14..20, 2023-05-21..06-08, 2024-01-30..02-11, 2024-12-25..27).
   That is 6.2% of the window. Enumerated in
   `outputs/reports/traffic_quality_report_full.md`. Phase 4 must carry a
   `traffic_missing` flag and never impute these as free-flowing traffic.
3. **24.6% of traffic readings are invalid** (`status = -101`, filler `speed = 0`)
   — 5,853,805 rows.
   Dropped by the named `invalid_status` rule — keeping them would drag every speed
   average toward zero.
4. **Events have no coordinates.** Free-text street descriptions plus borough /
   community board / precinct. **19,011 distinct location strings** need geocoding
   before events map to H3 cells — a sized, scheduled Phase 4 task.
5. **Events dataset is permits only** — no ticketed arena events (MSG, Barclays).
   Documented limitation.
6. **No station capacity data.** As planned, Phase 8 estimates capacity statistically.
7. **`visibility` unavailable** from the Open-Meteo archive (100% null); removed from
   the requested variables rather than kept as a dead column.
8. **`phase_02` spec was never supplied.** `docs/phases/phase_02_spatial_panel.md` is
   a reconstruction from the references in phases 3-8 and CLAUDE.md. Replace it if the
   original turns up — confirm the target definitions before building on it.

---

## Running log

- **2026-08-25** — Phase 2 complete. `SpatialIndexer` + `H3Indexer`, active-region
  selection, and the dense 104M-row panel with h1-h4 targets built and gated
  (11/11). Dev sample verified before the full range. Gate and tests green.
- **2026-08-24** — Phase 1 complete. Repo scaffolded; configs written; 90 Citi Bike
  CSVs ingested (79,410,195 rows → 2.5 GB Parquet in 2.0 min via Polars); weather,
  events and traffic pulled; cleaning rules, quality reports, global chronological
  sort and the test suite implemented; station registry built; dev sample carved.
  Every stage was verified on the 7-day dev sample before touching two years, per
  CLAUDE.md rule 5. Two real bugs found by the tests and fixed (see above).
