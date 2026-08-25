# Phase 5 - Spatial Representation Experiments (H3 resolution + H3 vs S2)

## Goal
Answer Research Questions 1 & 2 with LightGBM only (keep the model constant so the
comparison is fair). This is one of the project's two headline results.

## Part A - H3 resolution study
1. Rerun the full Phase 2-4 pipeline for H3-8, H3-9, H3-10 with identical dates,
   weather, features, model config, split, and metrics.
2. Report: MAE/RMSE/WAPE/Hotspot-F1 per resolution, plus active region count,
   zero-demand %, mean/median trips per region, processing time.
3. Pick the best resolution using forecast performance + reasonable sparsity - not
   cell-size intuition alone.

## Part B - S2 matching (only after best H3 is chosen)
1. Calculate median H3 cell area for the active NYC region at the winning resolution.
2. Test nearby S2 levels, compute median area, active cell count, trips/cell.
3. Pick the S2 level whose granularity best matches H3 (area difference + weighted
   active-cell-count difference, log-ratio scale for scale independence, weights
   configurable).
4. Implement `S2Indexer` against the same `SpatialIndexer` interface from Phase 2.

## Part C - H3 vs S2 experiment
Run the identical LightGBM pipeline on both. Compare: MAE/RMSE/WAPE/Hotspot-F1,
zero-demand %, region count, median trips/region, feature-build time, training time,
inference time, storage size, and whether neighbor features behave similarly.

## Definition of Done
- [x] H3-8/9/10 comparison table generated, best resolution chosen and justified
- [x] S2 level selected via matching procedure, not guessed
- [x] H3 vs S2 comparison table generated with both accuracy and efficiency columns
- [x] Results saved to `outputs/experiments/`
- [x] `docs/STATUS.md` updated, phase committed to git

## Note on scope
This phase (plus TFT/ST-GNN in Phase 6) is the part of the plan that goes beyond a
lean v1 - it is real, valuable research, but it roughly doubles project time versus
H3-only. Make sure that tradeoff is still the one you want before starting Part B/C.
