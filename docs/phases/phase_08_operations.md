# Phase 8 - Inventory, Shortage Detection, Rebalancing, Final Artifacts

## Goal
Answer Research Question 4 - turn forecasts into operational decisions and measure
whether that actually helps.

## Station capacity
Prefer real capacity data if available - else a current snapshot as a labeled proxy
(`capacity_source = current_proxy`) - else statistically estimate via q95 of daily
cumulative net-flow range (`F(t) = cumulative(dropoffs - pickups)`), calibrated
against any known capacities. Impute missing capacity by trip-volume decile, not a
flat constant.

## Daily inventory reconstruction (reset per day, do not chain two years)
For each station/day, find the feasible starting-inventory interval
`[max(0, -min(F)), min(C, C - max(F))]` and pick the point closest to 50% capacity.
If infeasible (staff intervened that day), solve a 1D optimization minimizing
below-zero + overflow + distance-from-50% penalties; log `inventory_fit_error` and
flag high-error days as unreliable. Aggregate station inventory/capacity up to
region level.

## Shortage / surplus detection
```
projected_inventory_H = current_inventory + cumulative predicted dropoffs
                                          - cumulative predicted pickups
shortage = max(safety_inventory - projected_inventory, 0)
surplus  = max(projected_inventory - target_inventory, 0)
```
`safety_inventory` and `target_inventory` are configurable (test 0/5/10% and ~50%
of capacity respectively) - do not hardcode without a sensitivity check.

## Rebalancing V1 - greedy
Sort shortages descending -> match each to nearest surplus region by centroid
distance -> move `min(shortage, available_surplus)` -> update both -> repeat. Never
exceed source surplus or destination capacity or produce negative inventory. Log
every move (timestamp, source, destination, bikes_moved, distance).

## Rebalancing evaluation
Simulate no-rebalancing vs. forecast-driven rebalancing against identical actual
future demand. Compare unserved pickup demand, dock overflow, empty/full-region
intervals, service level, bikes moved, distance. **A model with slightly worse MAE
can still win operationally** - report both forecast and operational metrics per
model, do not assume the lowest-MAE model is automatically the best rebalancer.

## Standardized output interface
```
predict(spatial_system, model_name, forecast_time, horizon) ->
region_id, forecast_time, horizon, predicted_pickups, predicted_dropoffs,
projected_inventory, shortage, surplus
```
This is backend-only - no UI in this phase, just clean, UI-ready output.

## Definition of Done
- [ ] Station/region capacity + daily inventory estimation implemented and documented
      as an approximation (not claimed as exact historical reconstruction)
- [ ] Shortage/surplus detection implemented with configurable thresholds
- [ ] Greedy rebalancing implemented with all constraints enforced
- [ ] No-rebalancing vs. forecast-driven comparison run, service-level metric reported
- [ ] Standardized prediction interface implemented and tested
- [ ] All artifacts (features, region metadata, graphs, models, scalers, metrics,
      inventory estimates, rebalancing results) saved and reproducible from config
- [ ] `docs/STATUS.md` updated, project marked complete per full Definition of Done
