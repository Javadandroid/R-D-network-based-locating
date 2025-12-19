from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from cellular.choices import DatasetSource


@dataclass(frozen=True)
class ProviderLookup:
    lat: float
    lon: float
    accuracy_m: Optional[float]
    raw: Optional[Dict[str, Any]]
    request_url: str
    request_body: Optional[Dict[str, Any]]


class ExternalTowerProvider:
    """External provider interface (Strategy)."""

    name: str
    dataset_source: str

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
        raise NotImplementedError


def normalize_radio_type(value: str) -> str:
    s = (value or "").strip().lower()
    if s in ("gsm", "2g"):
        return "gsm"
    if s in ("umts", "wcdma", "3g"):
        return "umts"
    if s in ("nr", "5g"):
        return "nr"
    # default
    return "lte"


def dataset_source_for(provider_name: str) -> str:
    mapping = {
        "COMBAIN": DatasetSource.COMBAIN,
        "GOOGLE": DatasetSource.GOOGLE,
    }
    return mapping.get(provider_name.upper(), DatasetSource.OTHER)

