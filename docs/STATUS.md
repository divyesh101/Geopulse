# STATUS

**Current phase:** 5 - Spatial representation experiments - **COMPLETE**
**State:** Phases 1-5 done. Phase 6 in progress: ST-GNN trained locally; TFT and the
matched-S2 deep runs move to Kaggle GPU.
**Next:** Phase 6 deep models on Kaggle -> Phase 7 (TEST) -> Phase 8 (operations).

---

## Phase 5 - Definition of Done (COMPLETE)

- [x] H3-8/9/10 comparison table generated, best resolution chosen and justified
- [x] S2 level selected via the matching procedure, not guessed
- [x] H3 vs S2 comparison with both accuracy and efficiency columns
- [x] Results saved to `outputs/experiments/phase5_spatial.json`
- [x] `docs/STATUS.md` updated, phase committed to git

### RQ1 - which H3 resolution?

Model and feature set held constant; identical training budget at every resolution.

| res | regions | area km2 | zero% | MAE(*) | WAPE(*) | naive MAE | **SKILL** | HotF1 |
|---|---|---|---|---|---|---|---|---|
| **H3-8** | 321 | 0.741 | 47.5% | 1.654 | 0.308 | 2.224 | **0.2563** | 0.748 |
| H3-9 | 1483 | 0.106 | 71.4% | 0.705 | 0.605 | 0.873 | 0.1920 | 0.590 |
| H3-10 | 2162 | 0.015 | 75.6% | 0.580 | 0.731 | 0.706 | 0.1791 | 0.481 |

**Winner: H3-8.**

**The metric choice here is the whole result, so it is stated explicitly.** No raw
accuracy metric is comparable across resolutions:

* **MAE falls automatically as cells shrink** - smaller cells hold smaller counts, so
  absolute errors shrink mechanically. Picking by MAE crowns H3-10 regardless of skill.
* **WAPE falls automatically as cells grow** - aggregation smooths relative error.
  Picking by WAPE crowns the coarsest grid, and in the limit a single cell.
* **Hotspot-F1 depends on region count** - the top 10% of 321 regions is a different
  task from the top 10% of 2,162.

The three disagree completely (MAE says H3-10, WAPE and Hotspot-F1 say H3-8), which is
the tell that none of them is measuring skill. **Skill vs Seasonal Naive at the same
resolution** (`1 - model_MAE / naive_MAE`) divides the scale effect out, because
numerator and denominator live on the same grid. On that measure H3-8 wins - and it
also wins the spec's second criterion, sparsity, at 47.5% zero-demand cells versus
75.6% at H3-10.

### RQ2 - H3 or S2?

S2 level **13** selected by the matching procedure: weighted log-ratio distance on
median cell area *and* active-cell count (score 0.319; next best L14 at 0.951).
Log-ratio so that "twice as coarse" and "twice as fine" cost the same.

| system | regions | area km2 | zero% | MAE | WAPE | naive MAE | SKILL | HotF1 | features MB | train s |
|---|---|---|---|---|---|---|---|---|---|---|
| H3-8 | 321 | 0.741 | 47.5% | 1.654 | 0.308 | 2.224 | 0.2563 | 0.748 | 430 | 32 |
| S2-13 | 231 | 1.088 | 42.1% | 2.002 | 0.269 | 2.757 | **0.2741** | 0.769 | 328 | 24 |

**S2-13 edges H3-8 on skill (0.274 vs 0.256) - but the honest reading is that the
spatial system barely matters.** S2-13 cells are still **47% larger** than H3-8's;
matched granularity is not identical granularity, because quadrilaterals cannot tile
to the same areas as hexagons. That residual coarseness plausibly accounts for the
entire 1.8-point gap. **Resolution is the decision that matters; H3 vs S2 is close to
a coin flip**, with S2 marginally cheaper to build (328 vs 430 MB, 24 vs 32 s).

---

## Phase 6 - in progress

**ST-GNN (H3-9), trained locally on CPU:** 52,936 parameters, 8 epochs, 99 minutes.
Best validation mean MAE **0.7149**; at h1 pickup **0.6917**, which slightly beats the
Phase 3 LightGBM's 0.6945 on the same target. A 53k-parameter graph model matching a
gradient-boosted ensemble is a real result for RQ3, though not yet a decisive one.

**Moving to Kaggle GPU.** `kaggle_upload/` (557 MB) contains bundles for H3-8 (the
Phase 5 winner) and S2-13 (matched), plus `src/models/deep.py` itself so the Kaggle
run cannot silently diverge from the repo, and a notebook that trains the 4-config
deep matrix `{H3-8, S2-13} x {ST-GNN, TFT}`. The LightGBM half of the matrix stays
local - it is CPU-bound and needs the 5.9 GB feature table.

---

## Phase 4 - Definition of Done (COMPLETE)

- [x] Each feature family implemented and leakage-tested individually (20 new tests)
- [x] Ablation table (A-H) generated -> `outputs/metrics/ablation_h39.parquet`
- [x] Final feature set decided **by the ablation**, not by assumption
- [x] `docs/STATUS.md` updated, phase committed to git

### The ablation result

168 features across 8 families, added cumulatively. Identical budget at every step:
4,345,190 train rows / 2,177,044 validation rows / 300 rounds, h1 targets.

| step | family | features | pickup MAE | dropoff MAE | mean dMAE | verdict |
|---|---|---|---|---|---|---|
| A | demand_recent | 21 | 0.7259 | 0.7208 | - | baseline |
| B | + calendar_seasonal | 76 | **0.6901** | **0.6864** | **+4.85%** | **HELPS** |
| C | + rolling_trend | 125 | 0.6889 | 0.6866 | +0.07% | marginal, kept |
| D | + weather | 142 | 0.6926 | 0.6901 | -0.52% | no benefit |
| E | + events | 148 | 0.6927 | 0.6902 | -0.01% | no effect |
| F | + traffic | 155 | 0.6928 | 0.6899 | +0.01% | no effect |
| G | + spatial_neighbor | 164 | 0.6930 | 0.6905 | -0.06% | no benefit |
| H | + station_network | 168 | 0.6928 | 0.6905 | +0.02% | no effect |

**Final feature set: A + B + C (125 features)**, recorded as
`advanced_features.final_families` in `configs/base.yaml`.

### What this answers

The phase existed to settle "did traffic and events actually help, or were they not
worth the pipeline complexity". The answer is unambiguous: **they did not**. Neither
did weather, spatial-neighbour aggregates, or station/network context. Nearly all the
signal beyond recent demand is **calendar and seasonality** - which is intuitive for
commuter cycling, and cheap.

Three caveats stated plainly, because they bound how far the result generalises:

1. **"Hurts" should be read as "no measurable benefit", not "actively harmful".**
   Every step gets the same 300 rounds, so adding 17 weather columns dilutes a fixed
   capacity budget. A -0.5% move at that scale is capacity dilution, not evidence
   that rain is anti-informative.
2. **Traffic never had a fair chance on coverage.** After fixing link attribution to
   use the whole polyline rather than the midpoint (18 -> 50 of 128 links), traffic
   still reaches only **76 of 1,483 regions (5.1%)**. The feature is null for 95% of
   rows, so the ablation is really measuring "traffic on 5% of Manhattan", not
   "traffic".
3. **Events carry a 25% geocoding hole.** 74.7% of event rows resolved; the rest are
   free-text locations GeoSearch could not place, or were rejected by the borough
   check. A better geocoder might change family E - though at +/-0.01% it would have
   to change it a lot.

Families D-H remain implemented, tested and reproducible. They are simply not
selected, and the decision can be revisited at another resolution in Phase 5.

### Phase 4 engineering notes

**`forecast_time` is now pinned down** in `docs/FORECAST_TIME_CONVENTION.md`: it is
the END of bin `ts`. That makes `h1` genuinely a 15-minute-ahead forecast (the other
reading would make it 15-30 minutes, and every horizon label in the project would be
off by one bin), and it makes the current bin's demand a legal input. Phase 3 omitted
that lag-0 term, which is part of why its numbers were flagged as a floor.

**A partitioned-write bug cost a rebuild.** polars' `write_parquet(partition_by=...)`
names every file `00000000.parquet` and rewrites the directory, so each region batch
silently replaced the previous one - only 35 of 1,483 regions survived. Writes now go
through DuckDB with a per-batch `FILENAME_PATTERN`, and the script asserts that the
row and region counts on disk match what was handed to the writer.

**The ablation loader sampled after `collect()`**, materialising 86M rows x 175
columns and running the machine out of memory. It now hashes `ts` inside the scan, so
the filter pushes down - and because it samples **whole timestamps**, the full region
cross-section survives at each retained instant, which Hotspot-F1 depends on.

---

## Phase 3 - Definition of Done (STOP-AND-VERIFY GATE: PASSED)

Verified by `scripts/14_phase3_check.py`.

- [x] Seasonal Naive computed for both variants, best one flagged
- [x] 8 LightGBM models trained (pickup/dropoff x h1-h4), predictions clipped >= 0
- [x] **LightGBM beats Seasonal Naive on validation MAE on 8/8 targets**
- [x] All leakage tests pass
- [x] All data-validation tests pass
- [x] Verified on the dev sample AND the full two-year data
- [x] `docs/STATUS.md` updated, phase committed to git

### Validation results (Sep-Oct 2024, 8,684,448 rows, TEST never touched)

| target | naive MAE | LightGBM MAE | improvement | RMSE | WAPE | Hotspot F1 |
|---|---|---|---|---|---|---|
| pickup_h1 | 0.8768 | **0.6945** | 20.8% | 1.342 | 0.596 | 0.602 |
| pickup_h2 | 0.8768 | **0.7013** | 20.0% | 1.364 | 0.602 | 0.600 |
| pickup_h3 | 0.8768 | **0.7049** | 19.6% | 1.380 | 0.605 | 0.598 |
| pickup_h4 | 0.8768 | **0.7076** | 19.3% | 1.388 | 0.608 | 0.598 |
| dropoff_h1 | 0.8673 | **0.6920** | 20.2% | 1.340 | 0.594 | 0.595 |
| dropoff_h2 | 0.8673 | **0.6984** | 19.5% | 1.364 | 0.600 | 0.592 |
| dropoff_h3 | 0.8673 | **0.7035** | 18.9% | 1.381 | 0.604 | 0.590 |
| dropoff_h4 | 0.8672 | **0.7072** | 18.5% | 1.394 | 0.607 | 0.589 |

Seasonal Naive variants, mean MAE: `same_week` **0.872** beats `same_day` 0.899 -
weekly seasonality dominates daily for bike demand, so `same_week` is the baseline.

### Phase 3 decisions

**The Seasonal Naive baseline is aligned correctly, which makes the gate harder.**
The naive forecast for `t + h` is the value one season before *that* instant, i.e.
`lag_{season - h}` - lag 95, not 96, for one-day seasonality at h=1. Those eight
extra lag columns are materialised **for the baseline only** and kept out of
`feature_columns`. Scoring the baseline off `lag_96` would have misaligned it by up
to an hour and handed LightGBM an unearned win.

**Features are basic on purpose.** 36 model inputs: 18 lags (1, 2, 4, 8, 12, 24, 96,
192, 672 steps x pickups/dropoffs), 11 calendar, 6 cyclical, plus `region_id` as a
categorical. Rolling, EWM, trend, seasonal-slot, weather, events, traffic and
neighbour families are Phase 4 - the gate should measure a clean baseline, not a
head start.

**One week of warm-up is dropped per region.** The longest lag is 672 steps, so the
first 672 rows of each region have null lags because there is no history, not
because demand was zero. 1,483 x 672 = 996,576 rows removed, leaving 103,074,432.

**Training subsamples; validation never does.** 104M rows x 36 features does not fit
in 16 GB as a dense matrix, so TRAIN uses a uniform 25% sample (21,418,969 rows)
while VALIDATION is scored in full (8,684,448 rows). Configurable via
`train.train_sample_frac`; Phase 6 revisits it when tuning.

**DST-flagged bins are excluded** (`train.exclude_dst_unreliable`), carrying the
Phase 1/2 finding through instead of learning the artificial collapse.

**Feature building is batched by region.** A single pass over 104M rows with 34 lag
windows plus a global sort spilled 12 GB and threatened to exhaust the disk. Lags are
`PARTITION BY region_id`, so batching by region is **exact** - 9 batches of ~12M rows
finished in 6.4 min with 4 KB of spill. This also makes the Phase 5 sweep feasible.

### Caveat to carry into Phase 6

**Every model hit the 500-round cap without early stopping firing** (best_iteration
500 for 7 of 8, 499 for one). The untuned baseline is still improving when it runs
out of rounds, so these numbers are a floor, not LightGBM's ceiling. Phase 6 should
raise `n_estimators` and let early stopping actually bind.

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

- **2026-08-25** — Phase 3 gate PASSED. 103M-row feature table (36 model inputs)
  built in region batches; Seasonal Naive (both variants) + 8 LightGBM models
  trained; LightGBM beats the better naive on 8/8 targets by 18.5-20.8% MAE.
  15 leakage tests re-derive every lag by independent timestamp join. 115 tests.
- **2026-08-25** — Phase 2 complete. `SpatialIndexer` + `H3Indexer`, active-region
  selection, and the dense 104M-row panel with h1-h4 targets built and gated
  (11/11). Dev sample verified before the full range. Gate and tests green.
- **2026-08-24** — Phase 1 complete. Repo scaffolded; configs written; 90 Citi Bike
  CSVs ingested (79,410,195 rows → 2.5 GB Parquet in 2.0 min via Polars); weather,
  events and traffic pulled; cleaning rules, quality reports, global chronological
  sort and the test suite implemented; station registry built; dev sample carved.
  Every stage was verified on the 7-day dev sample before touching two years, per
  CLAUDE.md rule 5. Two real bugs found by the tests and fixed (see above).
