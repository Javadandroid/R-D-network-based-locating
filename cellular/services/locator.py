from __future__ import annotations

from typing import Any, Dict, List

from cellular.services.tower_resolver import TowerResolver
from cellular.utils.cleaners import clean_cells
from cellular.utils.geometry import (
    calculate_distance,
    calculate_new_coordinates,
    distance_from_ta,
    estimate_bearing,
    trilaterate_three,
    trilaterate_two_towers,
    weighted_centroid,
)


def locate_cells(
    cells_data: List[Dict[str, Any]],
    *,
    reference_lat: float | None = None,
    reference_lon: float | None = None,
    allow_external_neighbors: bool = False,
    allow_external_serving: bool = True,
) -> Dict[str, Any]:
    """
    Core locate algorithm.

    - Cleans input cells
    - Resolves towers (DB first; optionally external providers)
    - Computes location based on 1 / 2 / 3+ towers
    """
    cells = clean_cells(cells_data)
    if not cells:
        raise ValueError("No valid cells after cleaning")

    resolver = TowerResolver(reference_lat=reference_lat, reference_lon=reference_lon)

    def _allow_external(cell: Dict[str, Any]) -> bool:
        return bool(allow_external_serving if cell.get("registered", True) else allow_external_neighbors)

    # Only keep cells that have a resolvable tower (no temporary fallback).
    resolved_cells: list[dict[str, Any]] = []
    resolved_towers: list[Any] = []
    resolved_sources: list[str] = []
    for c in cells:
        res = resolver.resolve(
            mcc=c.get("mcc"),
            mnc=c.get("mnc"),
            cell_id=c.get("cellId"),
            lac=c.get("lac"),
            pci=c.get("pci"),
            earfcn=c.get("earfcn"),
            signal_strength=c.get("signalStrength"),
            allow_external=_allow_external(c),
        )
        if res.tower is None:
            continue
        resolved_cells.append(c)
        resolved_towers.append(res.tower)
        resolved_sources.append(res.source)

    if not resolved_cells:
        raise ValueError("No towers found in database for provided cells")

    # 1 tower
    if len(resolved_cells) == 1:
        c = resolved_cells[0]
        tower_obj = resolved_towers[0]
        source = resolved_sources[0]

        rsrp = c.get("signalStrength")
        ta = c.get("timingAdvance")

        ta_dist = distance_from_ta(ta)
        bearing_used: float | None = None
        confidence = "medium"

        if ta_dist is not None:
            radius = ta_dist
            bearing_used = (
                float(getattr(tower_obj, "antenna_azimuth", 0.0))
                if getattr(tower_obj, "antenna_azimuth", None) is not None
                else float(estimate_bearing(tower_obj.cell_id))
            )
            coords = calculate_new_coordinates(tower_obj.lat, tower_obj.lon, radius, bearing_used)
            final_lat = coords["lat"]
            final_lon = coords["lon"]
            confidence = "high"
        else:
            if rsrp is not None and rsrp > -70:
                final_lat = tower_obj.lat
                final_lon = tower_obj.lon
                radius = 100.0
                confidence = "high"
            else:
                radius = calculate_distance(rsrp, tx_power=getattr(tower_obj, "tx_power", None))
                bearing_used = (
                    float(getattr(tower_obj, "antenna_azimuth", 0.0))
                    if getattr(tower_obj, "antenna_azimuth", None) is not None
                    else float(estimate_bearing(tower_obj.cell_id))
                )
                coords = calculate_new_coordinates(tower_obj.lat, tower_obj.lon, radius, bearing_used)
                final_lat = coords["lat"]
                final_lon = coords["lon"]
                confidence = "low" if rsrp is None or rsrp <= -100 else "medium"

        return {
            "location": {
                "lat": round(final_lat, 7),
                "lon": round(final_lon, 7),
                "google": f"{round(final_lat, 7)},{round(final_lon, 7)}",
            },
            "radius": round(radius, 2),
            "debug": {
                "source": source,
                "bearing_used": float(bearing_used or 0.0),
                "signal": rsrp,
                "confidence": confidence,
            },
        }

    # 2 towers
    if len(resolved_cells) == 2:
        towers_info = []
        for idx, c in enumerate(resolved_cells):
            t = resolved_towers[idx]
            towers_info.append({"lat": t.lat, "lon": t.lon, "rsrp": c["signalStrength"]})

        centroid = trilaterate_two_towers(towers_info[0], towers_info[1])
        if centroid is None:
            raise RuntimeError("Unable to compute centroid")

        radius = max(50.0, round(min(calculate_distance(c["signalStrength"]) for c in resolved_cells), 2))
        return {
            "location": {
                "lat": round(centroid["lat"], 7),
                "lon": round(centroid["lon"], 7),
                "google": f"{round(centroid['lat'], 7)},{round(centroid['lon'], 7)}",
            },
            "radius": radius,
            "debug": {"source": "COMPOSITE", "bearing_used": None, "signal": None},
        }

    # 3+ towers
    sorted_idxs = sorted(range(len(resolved_cells)), key=lambda i: resolved_cells[i]["signalStrength"], reverse=True)
    top3 = sorted_idxs[:3]
    tower_objs: List[Dict[str, Any]] = []
    for i in top3:
        c = resolved_cells[i]
        t = resolved_towers[i]
        radius = calculate_distance(c["signalStrength"], tx_power=getattr(t, "tx_power", None))
        tower_objs.append({"lat": t.lat, "lon": t.lon, "radius": radius, "rsrp": c["signalStrength"], "rsrq": c.get("rsrq")})

    if len(tower_objs) < 3:
        towers_info = []
        for idx, c in enumerate(resolved_cells):
            t = resolved_towers[idx]
            towers_info.append({"lat": t.lat, "lon": t.lon, "rsrp": c["signalStrength"]})
        centroid = weighted_centroid(towers_info)
        if centroid is None:
            raise ValueError("No towers found in database for provided cells")
        return {
            "location": {
                "lat": round(centroid["lat"], 7),
                "lon": round(centroid["lon"], 7),
                "google": f"{round(centroid['lat'], 7)},{round(centroid['lon'], 7)}",
            },
            "radius": round(max(calculate_distance(c["signalStrength"]) for c in resolved_cells), 2),
            "debug": {"source": "FALLBACK_CENTROID", "bearing_used": None, "signal": None},
        }

    trilat = trilaterate_three(tower_objs[0], tower_objs[1], tower_objs[2])
    if trilat:
        final_lat, final_lon = trilat
        radius = min(t["radius"] for t in tower_objs)
        return {
            "location": {
                "lat": round(final_lat, 7),
                "lon": round(final_lon, 7),
                "google": f"{round(final_lat, 7)},{round(final_lon, 7)}",
            },
            "radius": round(radius, 2),
            "debug": {"source": "TRILATERATION", "bearing_used": None, "signal": None},
        }

    towers_info = []
    for idx, c in enumerate(resolved_cells):
        t = resolved_towers[idx]
        towers_info.append({"lat": t.lat, "lon": t.lon, "rsrp": c["signalStrength"]})
    centroid = weighted_centroid(towers_info)
    if centroid is None:
        raise ValueError("No towers found in database for provided cells")

    return {
        "location": {
            "lat": round(centroid["lat"], 7),
            "lon": round(centroid["lon"], 7),
            "google": f"{round(centroid['lat'], 7)},{round(centroid['lon'], 7)}",
        },
        "radius": round(max(calculate_distance(c["signalStrength"]) for c in resolved_cells), 2),
        "debug": {"source": "FALLBACK_CENTROID", "bearing_used": None, "signal": None},
    }


def build_anchor_markers(
    cells_data: List[Dict[str, Any]],
    limit: int = 20,
    *,
    reference_lat: float | None = None,
    reference_lon: float | None = None,
    allow_external_neighbors: bool = False,
    allow_external_serving: bool = True,
) -> List[Dict[str, Any]]:
    """
    Best-effort: resolve first N cells to tower markers for visualization.
    """
    cells = clean_cells(cells_data)
    resolver = TowerResolver(reference_lat=reference_lat, reference_lon=reference_lon)

    anchors: List[Dict[str, Any]] = []
    for idx, c in enumerate(cells[: max(0, int(limit))]):
        allow_external = allow_external_serving if c.get("registered", True) else allow_external_neighbors
        res = resolver.resolve(
            mcc=c.get("mcc"),
            mnc=c.get("mnc"),
            cell_id=c.get("cellId"),
            lac=c.get("lac"),
            pci=c.get("pci"),
            earfcn=c.get("earfcn"),
            signal_strength=c.get("signalStrength"),
            allow_external=bool(allow_external),
        )
        if res.tower is None:
            continue

        anchors.append(
            {
                "id": f"snap:{idx}",
                "radio_type": c.get("radio_type"),
                "mcc": c.get("mcc"),
                "mnc": c.get("mnc"),
                "lac": c.get("lac"),
                "cell_id": c.get("cellId"),
                "pci": c.get("pci"),
                "earfcn": c.get("earfcn"),
                "lat": float(getattr(res.tower, "lat", 0.0)),
                "lon": float(getattr(res.tower, "lon", 0.0)),
                "tx_power": getattr(res.tower, "tx_power", None),
                "source": res.source,
                "rsrp": c.get("signalStrength"),
            }
        )
    return anchors

