from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from cellular.services.providers.base import ExternalTowerProvider, ProviderLookup, normalize_radio_type


@dataclass(frozen=True)
class CombainLookupResult:
    lat: float
    lon: float
    accuracy_m: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None


def lookup_combain_cell(
    *,
    api_key: str,
    mcc: int,
    mnc: int,
    lac: Optional[int],
    cell_id: int,
    radio_type: str = "LTE",
    signal_strength: Optional[int] = None,
    request_id: Optional[str] = None,
    timeout_s: float = 10.0,
) -> Optional[CombainLookupResult]:
    """
    Query Combain geolocation API for a single cell tower.

    Expected response (example):
        {"location": {"lat": 35.755273, "lng": 51.4103}, "accuracy": 1234}
    """
    base_url = "https://apiv2.combain.com"
    params: Dict[str, str] = {"key": api_key}
    if request_id:
        params["id"] = str(request_id)

    cell: Dict[str, Any] = {
        "mobileCountryCode": int(mcc),
        "mobileNetworkCode": int(mnc),
        "cellId": int(cell_id),
    }
    if lac is not None:
        cell["locationAreaCode"] = int(lac)
    if signal_strength is not None:
        cell["signalStrength"] = int(signal_strength)

    payload = {
        "radioType": str(radio_type).upper(),
        "cellTowers": [cell],
    }

    resp = requests.post(base_url, params=params, json=payload, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()

    location = (data or {}).get("location") or {}
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None

    accuracy = data.get("accuracy")
    try:
        accuracy_f = float(accuracy) if accuracy is not None else None
    except Exception:
        accuracy_f = None

    return CombainLookupResult(lat=float(lat), lon=float(lng), accuracy_m=accuracy_f, raw=data)


class CombainProvider(ExternalTowerProvider):
    name = "COMBAIN"
    dataset_source = "COMBAIN"

    def __init__(self, *, api_key: str):
        self.api_key = api_key

    def lookup(
        self,
        *,
        mcc: int,
        mnc: int,
        lac: Optional[int],
        cell_id: int,
        radio_type: str,
        signal_strength: Optional[int],
        timeout_s: float,
    ) -> Optional[ProviderLookup]:
        request_url = "https://apiv2.combain.com"
        params: Dict[str, str] = {"key": self.api_key}

        cell: Dict[str, Any] = {
            "mobileCountryCode": int(mcc),
            "mobileNetworkCode": int(mnc),
            "cellId": int(cell_id),
        }
        if lac is not None:
            cell["locationAreaCode"] = int(lac)
        if signal_strength is not None:
            cell["signalStrength"] = int(signal_strength)

        request_body = {
            "radioType": normalize_radio_type(radio_type).upper(),
            "cellTowers": [cell],
        }

        resp = requests.post(request_url, params=params, json=request_body, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()

        location = (data or {}).get("location") or {}
        lat = location.get("lat")
        lng = location.get("lng")
        if lat is None or lng is None:
            return None

        accuracy = data.get("accuracy")
        try:
            accuracy_f = float(accuracy) if accuracy is not None else None
        except Exception:
            accuracy_f = None

        return ProviderLookup(
            lat=float(lat),
            lon=float(lng),
            accuracy_m=accuracy_f,
            raw=data,
            request_url=request_url,
            request_body=request_body,
        )
