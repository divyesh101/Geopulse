# Phase 4 - Full Feature Engineering + Ablation Study

## Goal
Add the remaining feature families on top of the Phase 3 baseline, and prove which
ones actually help via ablation - don't just assume more features = better.

## Feature families to add
- **Rolling stats** (1h/3h/6h/24h/7d windows): mean, std, sum (skip min/max unless
  they show value) for pickups and dropoffs.
- **EWM features** (1h/3h/24h) for faster-reacting recency weighting.
- **Trend/momentum**: 15m/30m/1h change, recent-vs-previous 1h mean delta, optional
  linear slope over last 1h/3h (keep only if it earns its cost in validation).
- **Horizon-aligned seasonal features**: same-slot-yesterday / same-slot-last-week
  per horizon (`pickup_seasonal_1d_h1` etc.) - computed per horizon since LightGBM
  trains one model per horizon.
- **Expanding seasonal expectations**: mean/median demand for this region at this
  weekday/time-slot, using only past data (expanding or rolling, never future).
- **Net-flow / inventory pressure**: net_flow lags, rolling net flow, pickup-minus-
  dropoff over 1h, dropoff/pickup ratio.
- **Future/target-time calendar features**: since horizon target times are known in
  advance, include target_hour_sin/cos, target_weekday, target_is_rush_hour, etc.
  per horizon. This is NOT leakage - calendar info is known ahead of time.
- **Weather**: join latest reading with `weather_timestamp <= forecast_time`, never a
  future reading. Derive is_raining, is_snowing, is_freezing, high_wind, temp change
  1h/3h. Missing values: forward-fill with a max gap, else train-set median, plus a
  `weather_missing` flag - fit any imputation stats on TRAIN only.
- **Spatial neighbor features**: first-ring H3 neighbor sum/mean/max of pickups and
  dropoffs, lagged and rolled versions, spatial gradient (own vs. neighbor mean).
  Test second-ring only as an experiment - keep it only if validation improves.
- **Station/network features**: active station count, station density, historical
  trip volume, capacity aggregates if available - computed without future-station
  leakage (a station only counts as active if it has already appeared historically).
- **Events**: map each NYC Permitted Event to its nearest H3 cell(s). Derive
  `event_present`, `event_count`, `distance_to_event`, `event_started_recently`,
  `event_ending_soon` per region/time-bin. Join using event start/end timestamps
  against `forecast_time` - only past/current events are known.
- **Traffic**: NYC DOT traffic-speed segments don't map 1:1 to H3 cells - assign
  each segment to a cell via midpoint or geometry overlap (document which method).
  Derive `traffic_speed_mean/min`, `congestion_index`, `travel_time_index`,
  `traffic_change_15m`. This family is a genuine unknown - let the ablation decide.
- **Optional (later ablation group only)**: member/casual share, bike-type share.

## Ablation study (mandatory)
Build progressively and report MAE/RMSE/WAPE/Hotspot-F1 at each step:
```
A: recent historical demand only
B: A + seasonal/calendar
C: B + rolling/trend
D: C + weather
E: D + events
F: E + traffic
G: F + spatial-neighbor
H: G + station/network
```
This directly answers "did traffic/events actually help, or were they not worth
the extra pipeline complexity" - a real, defensible result either way.

## Definition of Done
- [ ] Each feature family implemented and leakage-tested individually
- [ ] Ablation table (A-H) generated and saved to `outputs/metrics/`
- [ ] Final feature set decided based on ablation results, not assumption
- [ ] `docs/STATUS.md` updated, phase committed to git
