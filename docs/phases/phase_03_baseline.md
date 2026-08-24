# Phase 3 - Minimal Baseline (STOP-AND-VERIFY GATE)

## Goal
The smallest possible end-to-end pipeline that produces a trustworthy number:
raw data -> panel -> basic features -> Seasonal Naive + a simple LightGBM -> metrics.
This is the most important phase to get right - everything later builds on it.
**Do not proceed to Phase 4 until this fully passes.**

## Tasks
1. Basic calendar features: hour, minute, day_of_week, day_of_month, week_of_year,
   month, is_weekend, is_holiday, is_business_day, is_morning_rush, is_evening_rush
   (rush windows configurable, default 07:00-10:00 / 16:00-19:00).
2. Cyclical encoding: `sin`/`cos` for time_of_day, day_of_week, day_of_year.
3. Basic lags only (defer rolling/seasonal-slot/trend to Phase 4): lag 1, 2, 4, 8,
   12, 24, 96, 192, 672 (in 15-min steps) for pickups and dropoffs.
4. Targets: pickup_h1..h4, dropoff_h1..h4 (see Phase 2 for definitions).
5. Chronological split: Train = Jan 2023 - Aug 2024, Validate = Sep-Oct 2024,
   Test = Nov-Dec 2024. Test is untouched until final model selection - not opened
   again until Phase 7.
6. Seasonal Naive baseline (same-time-yesterday and same-time-last-week; use
   whichever performs better on validation).
7. One simple LightGBM per (target, horizon) - 8 models total - no tuning yet.
8. Leakage tests: for every feature, assert its latest source timestamp <=
   `forecast_time`. Specifically test lags, target shifting, and the train/val/test
   split itself (no scaler/statistic fit on val or test data).
9. Data validation tests: sorted timestamps, no duplicate region/timestamp rows,
   pickups/dropoffs >= 0, exactly one row per active region per interval.

## Definition of Done
- [ ] Seasonal Naive computed and reported (both variants, best one flagged)
- [ ] 8 LightGBM models trained (pickup/dropoff x h1-h4), predictions clipped >= 0
- [ ] LightGBM beats Seasonal Naive on validation MAE - if it doesn't, stop and
      investigate before adding complexity, don't paper over it with more features
- [ ] All leakage tests pass - treat any failure as a blocking bug, not a warning
- [ ] All data validation tests pass
- [ ] Verified on dev sample AND the full two-year (2023-2024) data
- [ ] `docs/STATUS.md` updated, phase committed to git

## Why this gate matters
A sophisticated model on a leaky/broken dataset is worthless. Nothing in Phase 4
onward should be started until this phase is boring, correct, and fully verified.
