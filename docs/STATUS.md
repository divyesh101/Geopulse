# STATUS

**Current phase:** 8 - Operations - **COMPLETE**
**State:** All eight phases done. TEST was opened exactly once, in Phase 7.
146 tests: 145 passing, 1 skipped.

**The four research questions, answered:**

| RQ | question | answer |
|---|---|---|
| 1 | which H3 resolution? | **H3-8**, chosen on skill vs Seasonal Naive - the only metric that survives a change of cell size |
| 2 | H3 or S2? | **near coin-flip.** S2-13 edges H3-8 on skill (0.274 vs 0.256) but its cells are 47% larger; resolution matters, the tiling scheme barely does |
| 3 | do TFT/ST-GNN beat tuned LightGBM? | **no.** LightGBM leads at both resolutions; TFT's WAPE and ST-GNN's Hotspot-F1 edges at H3-8 both reverse at S2-13. Caveat: the deep models were stopped undertrained at 8 epochs |
| 4 | do better forecasts improve operations? | **yes among forecasts, no in absolute terms** - LightGBM beats even perfect foresight by moving less, but rebalancing itself does not pay at region granularity |

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

## Phase 8 - Operations: inventory, shortage, rebalancing (COMPLETE)

- [x] Capacity + daily inventory estimated and documented **as an approximation**
- [x] Shortage/surplus detection with configurable thresholds (0%, 5%, 10% tested)
- [x] Greedy rebalancing with all constraints enforced
- [x] No-rebalancing vs forecast-driven comparison run, service level reported
- [x] Standardized prediction interface implemented and tested (`src/serving/predict.py`)
- [x] All artifacts saved and reproducible from config

### Capacity and inventory (both estimated - no dock data exists)

Citi Bike publishes no historical dock occupancy for 2023-2024, so capacity is the
q95 of each station's daily cumulative net-flow range: **median 15 docks, p10 8,
p90 53**, across 1,496,558 station-days and 2,459 stations. 2,387 stations were
sized from their own flow; 72 low-volume ones fell back to their volume-decile
median. Daily starting inventory is reconstructed per station-day inside the
feasible interval, reset each day rather than chained across two years. **1.73% of
station-days are infeasible without assuming staff intervened** and are flagged
`inventory_unreliable`; median fit error is 0.00.

### Rebalancing simulation (14 days of TEST, 1,348 steps x 321 regions)

| forecast | safety | service level | unserved | overflow | bikes moved | moves |
|---|---|---|---|---|---|---|
| no rebalancing | - | **0.9958** | **8,540** | **6,286** | 0 | 0 |
| perfect foresight | 5% | 0.9940 | 12,294 | 11,432 | 9,286 | 2,615 |
| **LightGBM** | 5% | **0.9942** | **11,904** | **10,782** | 7,720 | 2,107 |
| Seasonal Naive | 5% | 0.9939 | 12,391 | 11,355 | 9,531 | 2,699 |
| perfect foresight | 10% | 0.9891 | 22,297 | 21,475 | 23,383 | 6,305 |
| LightGBM | 10% | 0.9898 | 20,957 | 19,969 | 20,743 | 5,814 |
| Seasonal Naive | 10% | 0.9891 | 22,235 | 21,291 | 23,468 | 6,402 |

At safety 0% no region ever projects below the floor, so no strategy moves anything
and all three reproduce the baseline exactly - a useful control that the harness is
consistent.

### RQ4 - do better forecasts produce better operations?

**Two answers, and the second one is the honest headline.**

**(a) Among forecasts, yes - and not in the direction anyone would guess.** At the 5%
safety threshold, LightGBM leaves **11,904** pickups unserved against perfect
foresight's **12,294** and Seasonal Naive's **12,391**. *A real model beats a perfect
forecast.* That is not a paradox: LightGBM systematically under-forecasts (73% of its
largest errors are under-predictions), so it triggers **2,107 moves instead of 2,615**
- and in a regime where moving is harmful, restraint wins. This is exactly the
failure mode the phase spec warned about, in a sharper form than expected: not merely
"the lowest-MAE model is not automatically the best rebalancer", but *the perfect
forecast is not the best rebalancer either*.

**(b) Rebalancing itself does not pay here, and the reason is structural.** Every
intervention makes service worse: unserved rises from 8,540 to 11,904 and overflow
from 6,286 to 10,782 at 5% safety. The cause is granularity, not the algorithm.
At H3-8, 321 regions aggregate 2,459 stations - roughly 7.7 stations and ~115 docks
per region - against a median of ~3 trips per 15-minute bin. **A region that large
essentially cannot run dry**, which is why the do-nothing baseline already serves
99.58%. There is almost no shortage to recover, so the greedy rule spends its moves
stripping bikes from regions above the 50% target (which need them later) to top up
regions below the safety floor (which are empty because they have no demand).

**The defensible conclusion: rebalancing value cannot be demonstrated at region
granularity with estimated capacity.** The bike-rebalancing problem is real, but it
lives at *station* level, and reconstructing station-level inventory well enough to
prove it needs dock occupancy data this project does not have. Reporting a positive
result here would have required tuning the thresholds until the sign flipped, which
is exactly the kind of thing this phase was written to prevent.

### Standardized prediction interface

`src/serving/predict.py` implements the Phase 8 contract as a single function:

```python
predict(spatial_system, model_name, forecast_time, horizon) ->
    region_id, forecast_time, horizon, predicted_pickups, predicted_dropoffs,
    projected_inventory, shortage, surplus
```

It serves `lightgbm_final` and both Seasonal Naive variants across H3 and S2, refuses
a `forecast_time` that is not on the 15-minute bin grid rather than silently rounding
it, and carries `inventory_estimated` on every row so a caller cannot mistake the
operational columns for measurements. 10 tests in `tests/test_serving.py` cover the
contract and the end-to-end path, including that `shortage`/`surplus` follow
arithmetically from `projected_inventory` and that no region is ever both short and
in surplus.

---

## Phase 7 - Evaluation on TEST (COMPLETE)

**TEST (Nov-Dec 2024) was opened exactly once**, by `scripts/23_evaluate_test.py`.
Every model, feature set, resolution and hyperparameter was chosen on validation
before this ran.

### Model comparison on TEST, H3-8 (1,877,208 rows)

| model | pickup h1 MAE | dropoff h1 MAE | pickup h1 WAPE | RMSE | Hotspot F1 |
|---|---|---|---|---|---|
| **LightGBM (tuned)** | **1.1408** | **1.1275** | 0.3573 | 2.2020 | 0.7248 |
| ST-GNN | 1.2024 | 1.1978 | 0.3686 | 2.4180 | **0.7260** |
| TFT | 1.2919 | 1.4969 | **0.3523** | 2.5071 | - |
| Seasonal Naive (same day) | 1.8430 | 1.8253 | 0.5771 | 4.1931 | 0.6265 |
| Seasonal Naive (same week) | 1.9575 | 1.9409 | 0.6130 | 4.4710 | 0.6380 |

Degradation with horizon is mild and monotone: LightGBM pickup MAE runs
1.1408 (h1) -> 1.1696 (h2) -> 1.2088 (h4), i.e. a one-hour forecast is only 6%
worse than a 15-minute one.

### Model comparison on TEST, S2-13 (1,350,888 rows)

| model | pickup h1 MAE | RMSE | WAPE | Hotspot F1 |
|---|---|---|---|---|
| **LightGBM (tuned)** | **1.3777** | 2.6385 | **0.3105** | **0.7485** |
| TFT | 1.4762 | 3.0362 | 0.3569 | - |
| ST-GNN | 1.4817 | 2.9806 | 0.3269 | 0.7449 |
| Seasonal Naive (same day) | 2.3458 | 5.3872 | 0.5286 | 0.6568 |
| Seasonal Naive (same week) | 2.5046 | 5.7625 | 0.5644 | 0.6693 |

### The six-config matrix, on skill vs Seasonal Naive

Raw MAE is not comparable across spatial systems - S2-13 cells are 47% larger than
H3-8's, so their counts are larger and every absolute error with them. Skill
(`1 - model_MAE / naive_MAE`, both measured on the same grid) divides that out.

| config | MAE | WAPE | Hotspot F1 | **skill vs naive** |
|---|---|---|---|---|
| **LightGBM @ S2-13** | 1.3777 | 0.3105 | 0.7485 | **0.4127** |
| LightGBM @ H3-8 | 1.1408 | 0.3573 | 0.7248 | 0.3810 |
| TFT @ S2-13 | 1.4762 | 0.3569 | - | 0.3707 |
| ST-GNN @ S2-13 | 1.4817 | 0.3269 | 0.7449 | 0.3683 |
| ST-GNN @ H3-8 | 1.2024 | 0.3686 | 0.7260 | 0.3476 |
| TFT @ H3-8 | 1.2919 | 0.3523 | - | 0.2990 |

**LightGBM is first at both resolutions, and the S2-13 ordering confirms Phase 5's
RQ2 result independently**: S2-13 scores higher skill than H3-8 for all three model
families, exactly as the Phase 5 LightGBM-only sweep predicted (0.274 vs 0.256).
Note this is *skill*, not accuracy - H3-8 still has the lower raw MAE, and the
Phase 5 caveat stands: S2-13's cells remain 47% coarser, which plausibly accounts
for the whole margin.

**The deep models' two wins at H3-8 do not replicate at S2-13.** TFT's WAPE
advantage (0.3523 vs LightGBM's 0.3573 at H3-8) reverses at S2-13 (0.3569 vs
0.3105), and ST-GNN's Hotspot-F1 edge (0.7260 vs 0.7248) likewise reverses (0.7449
vs 0.7485). Two thin wins that vanish under a change of spatial system are better
read as noise than as architecture effects - which is the main reason the RQ3
answer below is stated as "not on MAE" rather than as a split decision.

### RQ3 - do TFT and ST-GNN beat a tuned LightGBM?

**No, not on MAE - but the answer is more interesting than the headline, and it
comes with a real caveat.**

1. **LightGBM wins absolute error at every horizon and both targets.** All three
   models beat both Seasonal Naive variants by 35-42%, so every one of them is a
   genuine model rather than a dressed-up persistence rule.
2. **At H3-8 only, TFT wins WAPE while losing MAE** (0.3523 vs 0.3573 at pickup
   h1), and **ST-GNN edges Hotspot-F1** (0.7260 vs 0.7248). Both land where their
   architectures predict - WAPE weights by volume, Hotspot-F1 ranks regions against
   each other, which is what the graph adjacency exists to inform.
3. **But neither win replicates at S2-13**, where LightGBM takes MAE, WAPE and
   Hotspot-F1 outright. Two sub-1% margins that flip under a change of tiling scheme
   are noise, not evidence. They are reported because suppressing them would be
   selective, not because they support a claim.

**The caveat, stated plainly: the deep models are undertrained.** Both were stopped
at 8 epochs on Kaggle and *both were still improving monotonically on the final
epoch* (TFT at S2-13 dropped 7% on its last epoch alone). LightGBM, by contrast,
ran to early-stopping convergence at 569-1101 boosting rounds. So this is
**"tuned LightGBM beats an 8-epoch TFT/ST-GNN"**, not "gradient boosting beats deep
learning on this problem". The honest reading is that LightGBM is the better
*value* here - it converged in 48 minutes of CPU and won - not that the deep models
were given their best shot.

### Error analysis - where LightGBM actually fails

**By hour of day** (pickup h1): worst at the afternoon peak - 16:00 MAE **1.809**,
17:00 1.768, 15:00 1.699 - and near-perfect overnight (03:00 MAE **0.281**). Error
tracks demand level almost exactly, which is expected for a count process.

**By demand tercile** - the sharpest result:

| band | MAE | actual mean | relative error |
|---|---|---|---|
| low | 0.404 | 0.00 | - |
| mid | 0.837 | 1.35 | 62% |
| high | **2.746** | **10.65** | **26%** |

Absolute error concentrates in busy cells; *relative* error is more than twice as
bad in the quiet ones. Which metric you quote decides which regions look broken.

**By weather**: rain MAE 0.853 vs dry 1.177 - but this is **not** the model doing
better in the rain. Mean actual demand is 1.57 in rain against 3.40 in dry
conditions; rain suppresses cycling, and a smaller count carries a smaller absolute
error. The apparent improvement is a demand effect, not a skill effect.

**Top-100 largest errors** are strikingly concentrated:
- **73% are under-forecasts** (mean actual 78.6 vs mean predicted 57.7)
- **38 of 100 occur at 16:00**, 18 at 18:00 - the afternoon commute
- they fall in just **22 distinct regions** out of 321

So the single characteristic failure is: **the model under-predicts afternoon-rush
spikes in a small set of very high-volume regions.** That is also the most
operationally expensive place to be wrong, and it is the concrete target for any
follow-up work (spike-aware loss, quantile heads, or per-region capacity terms).

### A baseline result that flipped between validation and TEST

On validation, `seasonal_naive_same_week` beat `same_day` (0.872 vs 0.899 mean MAE),
and Phase 3 adopted it as the baseline. **On TEST the order reverses**: same_day
1.8430 beats same_week 1.9575 at pickup h1. Nov-Dec contains Thanksgiving and
Christmas, which break week-over-week seasonality far more than day-over-day. Both
are reported rather than quietly picking the flattering one.

---

## Phase 6 - Advanced Models (COMPLETE)

- [x] LightGBM tuned, explainability artifacts saved
- [x] TFT trains, produces sane multi-horizon output, beats Seasonal Naive
- [x] ST-GNN trains, uses real spatial adjacency, beats Seasonal Naive
- [x] All six final configs trained: {H3-8, S2-13} x {LightGBM, TFT, ST-GNN}
- [x] Model artifacts, scalers and experiment metadata saved
- [x] `docs/STATUS.md` updated, phase committed to git

### LightGBM finalisation (H3-8)

**Objective was tested, not assumed**: Poisson 1.5695 vs `regression_l1` 1.5739 on
validation -> Poisson kept. **The Phase 3 round cap was the binding constraint it
was flagged as** - freed to 2,000 rounds with early stopping, the final models
stopped at 569-1,101 iterations, all genuinely converged.

Bounded Optuna search (10 trials, `pickup_h1`): 1.5695 -> **1.5544**. Mean
validation MAE across all 8 targets **1.5743**; on TEST, pickup h1 reaches 1.1408.

Gain-based feature importance is dominated by exactly the families the ablation
kept: `pickups_ewm_4`, `pickups_roll_mean_4`, `pickups_lag_0`,
`pickups_slot_expanding_mean` - families C, A and B respectively. Full ranking in
`outputs/metrics/feature_importance_h38.json`.

### The deep half, trained on a Kaggle T4

Four configs, `{H3-8, S2-13} x {ST-GNN, TFT}`, 8 epochs each, ~23 GPU-minutes total.
Best validation MAE (averaged over all 4 horizons and both targets):

| model | tag | params | best valid MAE | converged? |
|---|---|---|---|---|
| TFT | H3-8 | 239,688 | **1.6716** | no - still improving |
| ST-GNN | H3-8 | 35,432 | 1.7646 | no - still improving |
| TFT | S2-13 | 239,688 | 1.9674 | no - still improving |
| ST-GNN | S2-13 | 35,432 | 2.1988 | no - still improving |

Note these validation figures average **all four horizons and both targets**, so
they are not directly comparable to the h1-only LightGBM numbers above; the TEST
table in Phase 7 is the like-for-like comparison.

`kaggle_upload/` ships `src/models/deep.py` itself rather than re-typing the
architectures into the notebook, so the GPU run cannot silently diverge from the
repo. Scaling statistics are fitted on TRAIN only and baked into each `meta.json`.

**One bug found and fixed in the deep evaluation loop**: validation was scored on
the first N anchors of the split, which is 1 September starting at midnight - almost
entirely empty overnight bins. That reported MAE 0.665 where the true figure was
1.271. Fixed with strided sampling across the whole validation period, in both
`scripts/21_train_deep.py` and the Kaggle notebook.

---

## Phase 4b - the ablation re-run at H3-8

Phase 4 ran the A-H ablation at H3-9. Phase 5 then chose H3-8, where traffic covers
**20.2% of regions instead of 5.1%** - so the ablation was re-run at the winning
resolution to give families D-H a fair test rather than inheriting a verdict from a
grid where the external data barely existed.

| family | features | pickup MAE | dropoff MAE | mean dMAE | verdict |
|---|---|---|---|---|---|
| A demand_recent | 21 | 1.6944 | 1.6675 | - | baseline |
| B + calendar_seasonal | 76 | **1.5791** | **1.5606** | **+6.60%** | **HELPS** |
| C + rolling_trend | 125 | 1.5695 | 1.5503 | +0.64% | HELPS |
| D + weather | 142 | 1.5703 | 1.5511 | -0.05% | no benefit |
| E + events | 148 | 1.5702 | 1.5516 | -0.01% | no effect |
| F + traffic | 155 | 1.5702 | 1.5531 | -0.05% | no effect |
| G + spatial_neighbor | 164 | 1.5675 | 1.5464 | +0.30% | helps slightly |
| H + station_network | 168 | 1.5684 | 1.5475 | -0.07% | no benefit |

**The H3-9 verdict survives at H3-8, and the traffic result is now much stronger.**
Quadrupling traffic coverage changed nothing: family F still contributes -0.05%.
That converts "traffic didn't help, but coverage was only 5%" into a defensible
negative result - the feature was given four times the reach and still earned
nothing.

**Final feature set remains A + B + C (125 features).** Family G is the one genuine
change (+0.30% at H3-8 versus -0.06% at H3-9), but the sets are cumulative, so
taking G would drag D, E and F in with it for a gain inside noise. Recorded as
`advanced_features.final_families` in `configs/base.yaml`.

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

- **2026-08-25** - **Phases 6-8 complete; project finished.** Ablation re-run at
  H3-8 (traffic coverage 20.2% vs 5.1%) confirmed A+B+C and turned the traffic null
  result from "thin coverage" into a real finding. LightGBM finalised at both H3-8
  and S2-13 (objective tested, Optuna, early stopping now binding). Deep matrix
  trained on a Kaggle T4. TEST opened once: LightGBM wins MAE, TFT wins WAPE, ST-GNN
  wins Hotspot-F1. Phase 8 found rebalancing does not pay at region granularity, and
  that LightGBM out-rebalances perfect foresight by moving less. Standardized
  `predict()` interface added with 10 tests. 146 tests, 145 passing.
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
