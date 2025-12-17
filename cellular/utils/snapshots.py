from __future__ import annotations

from typing import Any, Dict, List, Optional

from cellular.utils.cleaners import SENTINEL_INT_MAX, SENTINEL_TAC, SENTINEL_CI


def extract_phone_location(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    loc = snapshot.get("location") or {}
    lat = loc.get("selected_latitude")
    lon = loc.get("selected_longitude")
    if lat is None or lon is None:
        return None
    return {
        "lat": float(lat),
        "lng": float(lon),
        "accuracy": loc.get("selected_accuracy"),
        "type": loc.get("selected_location_type"),
        "timestamp": snapshot.get("timestamp"),
    }


def infer_default_mcc_mnc(snapshot: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
    """
    Infer MCC/MNC for neighbor cells when the device reports sentinel values.
    Uses raw_data.cellTowerInfo.simOperator (e.g., "43235" -> mcc=432, mnc=35).
    """
    raw = snapshot.get("raw_data") or {}
    cti = raw.get("cellTowerInfo") or {}
    sim_operator = cti.get("simOperator") or cti.get("networkOperator")
    if not sim_operator:
        # Fallback: infer from serving (registered) cells if present.
        for item in (cti.get("allCellInfo") or []):
            if not isinstance(item, dict):
                continue
            if item.get("registered") is False:
                continue
            mcc = _to_int(item.get("mcc"))
            mnc = _to_int(item.get("mnc"))
            if mcc not in (None, SENTINEL_INT_MAX) and mnc not in (None, SENTINEL_INT_MAX):
                return mcc, mnc
        return None, None
    s = str(sim_operator).strip()
    if not s.isdigit() or len(s) < 4:
        return None, None
    try:
        mcc = int(s[:3])
        mnc = int(s[3:])
        return mcc, mnc
    except Exception:
        return None, None


def _to_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return None


def _to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def extract_cells_from_snapshot(
    snapshot: Dict[str, Any],
    *,
    registered_only: bool = True,
    max_cells: int = 12,
) -> List[Dict[str, Any]]:
    """
    Extract a compact list of cells (in the format expected by locate_cells)
    from snapshot raw_data.cellTowerInfo.allCellInfo.
    """
    raw = snapshot.get("raw_data") or {}
    cti = raw.get("cellTowerInfo") or {}
    all_cells = cti.get("allCellInfo") or []
    default_mcc, default_mnc = infer_default_mcc_mnc(snapshot)

    extracted: List[Dict[str, Any]] = []
    for item in all_cells:
        if not isinstance(item, dict):
            continue
        if registered_only and item.get("registered") is False:
            continue

        cell_type = (item.get("type") or "").lower()
        mcc = _to_int(item.get("mcc"))
        mnc = _to_int(item.get("mnc"))
        if mcc in (None, SENTINEL_INT_MAX) and default_mcc is not None:
            mcc = default_mcc
        if mnc in (None, SENTINEL_INT_MAX) and default_mnc is not None:
            mnc = default_mnc

        # LTE
        registered = item.get("registered")

        if "lte" in cell_type:
            cell_id = _to_int(item.get("ci") or item.get("cellId") or item.get("cell_id"))
            lac = _to_int(item.get("tac") or item.get("lac"))
            if lac in (SENTINEL_TAC, SENTINEL_INT_MAX):
                lac = None
            pci = _to_int(item.get("pci"))
            earfcn = _to_int(item.get("earfcn"))
            rsrp = _to_int(item.get("rsrp") or item.get("dbm") or item.get("signalStrength"))
            rsrq = _to_int(item.get("rsrq"))
            ta = _to_int(item.get("ta") or item.get("timingAdvance"))

            extracted.append(
                {
                    "radio_type": "lte",
                    "cellId": cell_id,
                    "mcc": mcc,
                    "mnc": mnc,
                    "lac": lac,
                    "pci": pci,
                    "earfcn": earfcn,
                    "signalStrength": rsrp,
                    "rsrq": rsrq,
                    "timingAdvance": ta,
                    "registered": registered,
                }
            )
            continue

        # UMTS/WCDMA
        if "wcdma" in cell_type or "umts" in cell_type:
            cell_id = _to_int(item.get("cid") or item.get("ci"))
            lac = _to_int(item.get("lac"))
            if lac in (SENTINEL_TAC, SENTINEL_INT_MAX):
                lac = None
            psc = _to_int(item.get("psc"))
            dbm = _to_int(item.get("dbm"))
            rsrq = _to_int(item.get("rsrq"))
            extracted.append(
                {
                    "radio_type": "umts",
                    "cellId": cell_id,
                    "mcc": mcc,
                    "mnc": mnc,
                    "lac": lac,
                    "pci": psc,
                    "earfcn": _to_int(item.get("uarfcn")),
                    "signalStrength": dbm,
                    "rsrq": rsrq,
                    "timingAdvance": None,
                    "registered": registered,
                }
            )
            continue

        # GSM (best-effort)
        if "gsm" in cell_type:
            cell_id = _to_int(item.get("cid") or item.get("ci"))
            lac = _to_int(item.get("lac"))
            if lac in (SENTINEL_TAC, SENTINEL_INT_MAX):
                lac = None
            dbm = _to_int(item.get("dbm"))
            rsrq = _to_int(item.get("rsrq"))
            extracted.append(
                {
                    "radio_type": "gsm",
                    "cellId": cell_id,
                    "mcc": mcc,
                    "mnc": mnc,
                    "lac": lac,
                    "pci": None,
                    "earfcn": _to_int(item.get("arfcn")),
                    "signalStrength": dbm,
                    "rsrq": rsrq,
                    "timingAdvance": _to_int(item.get("mTa") or item.get("ta") or item.get("timingAdvance")),
                    "registered": registered,
                }
            )
            continue

    # keep only valid-ish, then trim
    extracted = [c for c in extracted if c.get("mcc") is not None and c.get("mnc") is not None and c.get("cellId") is not None]
    extracted.sort(key=lambda c: (c.get("signalStrength") is None, c.get("signalStrength", -9999)), reverse=True)
    return extracted[: max(1, int(max_cells))]
