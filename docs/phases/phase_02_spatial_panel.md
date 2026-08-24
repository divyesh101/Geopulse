# Phase 2 - Spatial Indexing + Demand Panel (RECONSTRUCTED SPEC)

> NOTE: the original `phase_02` file was not supplied with the other phase docs.
> This is reconstructed from the references to Phase 2 made in phases 3-8 and
> CLAUDE.md. If the original turns up, replace this file with it.

## Goal
Turn cleaned trips into a dense, gap-free (region x 15-min interval) demand panel,
behind a pluggable spatial-index interface so H3 and S2 are interchangeable later.

## SpatialIndexer interface
```python
class SpatialIndexer(Protocol):
    name: str                                   # "h3" | "s2"
    resolution: int
    def index(self, lat, lng) -> str: ...       # point -> region_id
    def neighbors(self, region_id, k=1) -> list[str]: ...
    def centroid(self, region_id) -> tuple[float, float]: ...
    def area_km2(self, region_id) -> float: ...
    def boundary(self, region_id) -> list[tuple[float, float]]: ...
```
`H3Indexer` is implemented in this phase; `S2Indexer` in Phase 5 against the same
interface.

## Tasks
1. Assign every trip a `start_region` and `end_region` at the configured resolution.
2. Define **active regions** from actual trip activity, not a station roster:
   a region is active if it has >= `min_trips` trips on >= `min_active_days` days
   (both configurable). Save region metadata (region_id, centroid, area, boundary,
   station count, total trips, first/last seen) to `data/spatial/`.
3. Build the demand panel at a configurable `interval_minutes` (default 15):
   - `pickups`  = count of trips whose `started_at` falls in the bin, by `start_region`
   - `dropoffs` = count of trips whose `ended_at`   falls in the bin, by `end_region`
   - `net_flow` = dropoffs - pickups
   Reindex to the full cartesian product of (active region x every interval in range)
   and fill missing with 0 - a region with no trips in a bin has demand 0, not NaN.
4. Targets, defined per horizon h in {1,2,3,4} = {15,30,45,60} min ahead:
   `pickup_h{h}[r,t]  = pickups[r,  t + h]`
   `dropoff_h{h}[r,t] = dropoffs[r, t + h]`
   Rows whose targets fall past the end of the data are dropped from training only.
5. Partition the panel by month to Parquet for cheap incremental reads.

## Definition of Done
- [ ] `SpatialIndexer` interface + `H3Indexer` implemented and unit-tested
- [ ] Active-region selection implemented, counts reported per resolution
- [ ] Dense panel built: exactly one row per active region per interval, no gaps
- [ ] Targets h1-h4 for pickups and dropoffs implemented and shift-tested
- [ ] Panel verified on the 7-day dev sample first, then the full range
- [ ] `docs/STATUS.md` updated, phase committed to git
