# Phase 6 - Advanced Models (LightGBM tuning -> TFT -> ST-GNN)

## Goal
Answer Research Question 3. Build the full model matrix (best-H3 x {LightGBM, TFT,
ST-GNN}) plus matched-S2 x same three. Get each model working and sane before
tuning the next - do not tune TFT and ST-GNN simultaneously.

## Step 1 - LightGBM finalize
- Test Poisson vs. standard regression objective on validation; keep the better one.
- Optuna search (num_leaves, max_depth, learning_rate, min_data_in_leaf,
  feature_fraction, bagging_fraction, lambda_l1/l2) - bounded search, not exhaustive.
- Clip predictions >= 0. Save best params, metrics, training time, feature importance
  (gain-based + optional SHAP on a sample), grouped by feature family.

## Step 2 - Temporal Fusion Transformer
- Inputs: static (region_id, network stats), known-future (calendar incl.
  target-time calendar), observed (historical demand, weather, net flow).
- Separate pickup/dropoff models if multi-target support is unstable.
- Encoder length: start at 96 steps (24h); test 48/96/192 only if compute allows.
- Loss preference: Negative Binomial -> Poisson -> Quantile fallback. Document choice.
  Clip final predictions >= 0 regardless of loss.
- Fit all scalers on TRAIN only; consider log1p for skewed inputs if it helps.

## Step 3 - Spatio-Temporal GNN (flagship model)
- Graph: node = region, edge = spatial adjacency (first-ring H3 / edge-neighbor S2).
  Pure spatial adjacency first, no dynamic OD-flow edges yet.
- Architecture: ~2 GAT layers + 1-2 GRU layers + MLP multi-horizon head. Do not
  build a large graph transformer.
- Temporal window: 24 steps (6h) + same-time-yesterday/last-week + calendar +
  weather as auxiliary inputs. Test 48 steps only if resources allow.
- Output: nodes x 4 horizons x 2 targets (pickup/dropoff), non-negative activation
  (Softplus). Loss: Poisson NLL or a robust regression loss - pick by validation
  metric, not training loss.
- Optional stretch only after the pure-adjacency version works: add historical
  TRAIN-only OD-flow as an edge feature and test if it helps.

## Fairness rule
All three models must have access to the same *categories* of information (past
demand, calendar, weather, spatial structure, network stats) - no model gets
privileged future information. Architecture-specific representation is fine.

## Definition of Done
- [x] LightGBM tuned, explainability artifacts saved
- [x] TFT trains, produces sane multi-horizon output, beats Seasonal Naive
- [x] ST-GNN trains, uses real spatial adjacency, beats Seasonal Naive
- [x] All six final configs trained: {best-H3, matched-S2} x {LightGBM, TFT, ST-GNN}
- [x] Model artifacts, scalers, and experiment metadata saved per Phase 8 schema
- [x] `docs/STATUS.md` updated, phase committed to git
