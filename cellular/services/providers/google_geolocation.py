from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from cellular.services.providers.base import ExternalTowerProvider, ProviderLookup, normalize_radio_type


@dataclass(frozen=True)
class GoogleGeolocationResult:
    lat: float
    lon: float
    accuracy_m: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None


def lookup_google_geolocation(
    *,
    api_key: str,
    mcc: int,
    mnc: int,
    lac: Optional[int],
    cell_id: int,
    signal_strength: Optional[int] = None,
    consider_ip: bool = False,
    timeout_s: float = 10.0,
) -> Optional[GoogleGeolocationResult]:
    """
    Query Google Geolocation API.

    Endpoint:
      https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}

    Example response:
      {"location":{"lat":35.750133,"lng":51.4697272},"accuracy":1823}
    """
    url = "https://www.googleapis.com/geolocation/v1/geolocate"
    params = {"key": api_key}

    tower: Dict[str, Any] = {
        "mobileCountryCode": int(mcc),
        "mobileNetworkCode": int(mnc),
        "cellId": int(cell_id),
    }
    if lac is not None:
        tower["locationAreaCode"] = int(lac)
    if signal_strength is not None:
        tower["signalStrength"] = int(signal_strength)

    payload = {
        "considerIp": bool(consider_ip),
        "cellTowers": [tower],
    }

    resp = requests.post(url, params=params, json=payload, timeout=timeout_s)
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

    return GoogleGeolocationResult(lat=float(lat), lon=float(lng), accuracy_m=accuracy_f, raw=data)


class GoogleGeolocationProvider(ExternalTowerProvider):
    name = "GOOGLE"
    dataset_source = "GOOGLE"

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
        request_url = "https://www.googleapis.com/geolocation/v1/geolocate"
        params = {"key": self.api_key}

        tower: Dict[str, Any] = {
            "mobileCountryCode": int(mcc),
            "mobileNetworkCode": int(mnc),
            "cellId": int(cell_id),
            "radioType": normalize_radio_type(radio_type),
        }
        if lac is not None:
            tower["locationAreaCode"] = int(lac)
        if signal_strength is not None:
            tower["signalStrength"] = int(signal_strength)

        request_body = {
            "considerIp": False,
            "cellTowers": [tower],
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
