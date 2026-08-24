"""S2 implementation of :class:`~src.spatial.base.SpatialIndexer` (Phase 5).

Deliberately the same interface as :class:`~src.spatial.h3_indexer.H3Indexer`, so the
H3-vs-S2 experiment swaps one object and changes nothing else about the pipeline.

Two honest differences from H3 that the comparison has to account for:

* **S2 cells are quadrilaterals with 4 edge neighbours**, not hexagons with 6. The
  "first ring" therefore means something slightly different. `neighbors()` returns
  edge neighbours by default, which is the closest analogue to H3's first ring.
* **There is no DuckDB S2 extension**, so `sql_index_expr` returns None and the
  pipeline falls back to indexing the (few thousand) distinct coordinates in Python
  and joining the lookup. That is the same work H3 does in-database, just moved -
  it does not change the result, only where it is computed.
"""

from __future__ import annotations

import math

import s2sphere

EARTH_RADIUS_KM = 6371.0088


class S2Indexer:
    name = "s2"

    def __init__(self, level: int) -> None:
        if level is None:
            raise ValueError(
                "S2 level is null - run the matching procedure in Phase 5 rather than "
                "guessing a level"
            )
        self.resolution = int(level)

    # `resolution` is the interface name; `level` reads better for S2
    @property
    def level(self) -> int:
        return self.resolution

    def _cell_id(self, region_id: str) -> s2sphere.CellId:
        return s2sphere.CellId.from_token(region_id)

    def index(self, lat: float, lng: float) -> str:
        cell = s2sphere.CellId.from_lat_lng(s2sphere.LatLng.from_degrees(lat, lng))
        return cell.parent(self.resolution).to_token()

    def neighbors(self, region_id: str, k: int = 1) -> list[str]:
        cell = self._cell_id(region_id)
        if k == 1:
            return sorted(n.to_token() for n in cell.get_edge_neighbors())
        seen = {cell}
        frontier = {cell}
        for _ in range(k):
            nxt: set[s2sphere.CellId] = set()
            for current in frontier:
                nxt.update(current.get_edge_neighbors())
            frontier = nxt - seen
            seen |= nxt
        return sorted(c.to_token() for c in seen if c != cell)

    def centroid(self, region_id: str) -> tuple[float, float]:
        point = self._cell_id(region_id).to_lat_lng()
        return (point.lat().degrees, point.lng().degrees)

    def area_km2(self, region_id: str) -> float:
        # exact_area() is in steradians on the unit sphere
        return s2sphere.Cell(self._cell_id(region_id)).exact_area() * EARTH_RADIUS_KM ** 2

    def boundary(self, region_id: str) -> list[tuple[float, float]]:
        cell = s2sphere.Cell(self._cell_id(region_id))
        corners = []
        for i in range(4):
            point = s2sphere.LatLng.from_point(cell.get_vertex(i))
            corners.append((point.lat().degrees, point.lng().degrees))
        return corners

    def sql_index_expr(self, lat_col: str, lng_col: str):
        """No DuckDB S2 extension - the caller indexes distinct coordinates in Python."""
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return f"S2Indexer(level={self.resolution})"


def average_area_km2(level: int) -> float:
    """Mean S2 cell area at a level - the sphere split into 6 * 4^level cells."""
    sphere_km2 = 4 * math.pi * EARTH_RADIUS_KM ** 2
    return sphere_km2 / (6 * 4 ** level)
