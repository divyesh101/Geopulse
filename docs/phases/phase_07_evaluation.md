# Phase 7 - Evaluation: Metrics, Hotspots, Model Comparison, Error Analysis

## Goal
Turn the six trained models into a defensible, complete evaluation story. This is
the only phase where the TEST set (Nov-Dec 2024) gets opened.

## Core metrics
MAE, RMSE, WAPE for pickups and dropoffs separately, reported at 15/30/60-min
horizons (45-min stays internal). Avoid MAPE - too many zero-demand regions.

## Region-level breakdowns
Global, per-region, per-hour-of-day, weekday vs weekend, high- vs low-demand
regions, rain vs no-rain - to see *where* the model fails, not just its average.

## Hotspot evaluation
Per-timestamp: actual hotspot = top 10% of regions by actual demand, predicted
hotspot = top 10% by predicted demand. Precision/Recall/F1 at each horizon.
Optional: Spearman rank correlation between predicted and actual regional demand.

## Model comparison matrix
```
Model            15m MAE   30m MAE   60m MAE   Hotspot F1
Seasonal Naive
LightGBM
TFT
ST-GNN
```
Run this for both H3 and matched-S2. Also track efficiency: feature-build time,
training time, inference time, artifact size - a model can win on accuracy and
still lose on practicality; report both.

## Error analysis (required, not optional)
Pull the top 100 largest errors, categorize by hour, weekday, weather, region,
demand intensity. Identify whether failures cluster around spikes, rain, rush
hour, weekends, or low-volume regions.

## Definition of Done
- [ ] Full metric tables generated for all six model x spatial configs
- [ ] Hotspot F1 computed at all three horizons
- [ ] Region-level breakdown tables/plots saved
- [ ] Error analysis written up with concrete failure patterns identified
- [ ] `docs/STATUS.md` updated, phase committed to git
