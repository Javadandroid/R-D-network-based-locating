from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from django.conf import settings

from cellular.choices import DatasetSource
from cellular.models import CellTower, TowerLookupLog
from cellular.services.providers.base import normalize_radio_type
from cellular.services.providers.combain import CombainProvider
from cellular.services.providers.google_geolocation import GoogleGeolocationProvider
from cellular.utils.cleaners import SENTINEL_CI, SENTINEL_INT_MAX, SENTINEL_TAC
from cellular.utils.geometry import haversine_distance

logger = logging.getLogger(__name__)


def _is_sentinel(value: Any) -> bool:
    return value in (None, SENTINEL_INT_MAX, SENTINEL_TAC, SENTINEL_CI)


@dataclass(frozen=True)
class ResolveResult:
    tower: Optional[CellTower]
    source: str


class TowerResolver:
    """
    Resolve a tower from local DB first, optionally falling back to paid providers.
    Includes a small in-memory cache to avoid repeated queries/calls per request.
    """

    def __init__(self, *, reference_lat: float | None = None, reference_lon: float | None = None):
        self.reference_lat = reference_lat
        self.reference_lon = reference_lon
        self._cache: Dict[Tuple[Any, ...], ResolveResult] = {}
        self._providers = []

        combain_key = (getattr(settings, "COMBAIN_API_KEY", "") or "").strip()
        google_key = (getattr(settings, "GOOGLE_GEOLOCATION_API_KEY", "") or "").strip()
        if combain_key:
            self._providers.append(CombainProvider(api_key=combain_key))
        if google_key:
            self._providers.append(GoogleGeolocationProvider(api_key=google_key))

    def resolve(
        self,
        *,
        radio_type: str | None = None,
        mcc: int | None,
        mnc: int | None,
        cell_id: int | None,
        lac: int | None,
        pci: int | None = None,
        earfcn: int | None = None,
        signal_strength: int | None = None,
        allow_external: bool = False,
    ) -> ResolveResult:
        cache_key = (radio_type, mcc, mnc, cell_id, lac, pci, earfcn, signal_strength, bool(allow_external))
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._resolve_uncached(
            radio_type=radio_type,
            mcc=mcc,
            mnc=mnc,
            cell_id=cell_id,
            lac=lac,
            pci=pci,
            earfcn=earfcn,
            signal_strength=signal_strength,
            allow_external=allow_external,
        )
        self._cache[cache_key] = result
        return result

    def _resolve_uncached(
        self,
        *,
        radio_type: str | None,
        mcc: int | None,
        mnc: int | None,
        cell_id: int | None,
        lac: int | None,
        pci: int | None,
        earfcn: int | None,
        signal_strength: int | None,
        allow_external: bool,
    ) -> ResolveResult:
        # 1) Local DB exact match (mcc/mnc/cell_id[/lac])
        tower = self._lookup_local_exact(mcc=mcc, mnc=mnc, cell_id=cell_id, lac=lac)
        if tower is not None:
            return ResolveResult(tower=tower, source="LOCAL_DB")

        # 2) Local DB signature (neighbor-style) lookup by PCI (+ optional EARFCN/LAC)
        tower = self._lookup_local_signature(mcc=mcc, mnc=mnc, pci=pci, earfcn=earfcn, lac=lac)
        if tower is not None:
            return ResolveResult(tower=tower, source="LOCAL_DB_SIGNATURE")

        # 3) Paid providers (Combain/Google) -> upsert into DB
        if allow_external:
            external = self._lookup_external_and_upsert(
                radio_type=radio_type,
                mcc=mcc,
                mnc=mnc,
                cell_id=cell_id,
                lac=lac,
                pci=pci,
                earfcn=earfcn,
                signal_strength=signal_strength,
            )
            if external is not None:
                return external

        return ResolveResult(tower=None, source="NOT_FOUND")

    def _lookup_local_exact(self, *, mcc: int | None, mnc: int | None, cell_id: int | None, lac: int | None) -> Optional[CellTower]:
        if _is_sentinel(mcc) or _is_sentinel(mnc) or _is_sentinel(cell_id):
            return None
        try:
            if lac is not None and not _is_sentinel(lac):
                try:
                    return CellTower.objects.get(mcc=int(mcc), mnc=int(mnc), cell_id=int(cell_id), lac=int(lac))
                except CellTower.DoesNotExist:
                    pass
            return CellTower.objects.filter(mcc=int(mcc), mnc=int(mnc), cell_id=int(cell_id)).first()
        except Exception as exc:
            logger.exception("Local DB lookup failed: %s", exc)
            return None

    def _lookup_local_signature(
        self,
        *,
        mcc: int | None,
        mnc: int | None,
        pci: int | None,
        earfcn: int | None,
        lac: int | None,
    ) -> Optional[CellTower]:
        if _is_sentinel(mcc) or _is_sentinel(mnc) or _is_sentinel(pci):
            return None
        try:
            qs = CellTower.objects.filter(mcc=int(mcc), mnc=int(mnc), pci=int(pci))
            if earfcn is not None and not _is_sentinel(earfcn):
                qs = qs.filter(earfcn=int(earfcn))
            if lac is not None and not _is_sentinel(lac):
                qs = qs.filter(lac=int(lac))

            candidates = list(qs.order_by("-updated_at")[:200])
            if not candidates:
                return None

            if self.reference_lat is None or self.reference_lon is None:
                return candidates[0]

            best: Optional[CellTower] = None
            best_d: Optional[float] = None
            for t in candidates:
                d = haversine_distance(self.reference_lat, self.reference_lon, t.lat, t.lon)
                if best_d is None or d < best_d:
                    best = t
                    best_d = d
            return best
        except Exception as exc:
            logger.exception("Signature lookup failed: %s", exc)
            return None

    def _lookup_external_and_upsert(
        self,
        *,
        radio_type: str | None,
        mcc: int | None,
        mnc: int | None,
        cell_id: int | None,
        lac: int | None,
        pci: int | None,
        earfcn: int | None,
        signal_strength: int | None,
    ) -> Optional[ResolveResult]:
        if _is_sentinel(mcc) or _is_sentinel(mnc) or _is_sentinel(cell_id):
            return None

        mcc_i = int(mcc)
        mnc_i = int(mnc)
        cell_id_i = int(cell_id)
        lac_i = None if lac is None or _is_sentinel(lac) else int(lac)
        pci_i = None if pci is None or _is_sentinel(pci) else int(pci)
        earfcn_i = None if earfcn is None or _is_sentinel(earfcn) else int(earfcn)

        if not self._providers:
            return None

        rt = normalize_radio_type(radio_type or "lte")

        for provider in self._providers:
            provider_name = getattr(provider, "name", "PROVIDER")
            request_url = ""
            request_body: Optional[Dict[str, Any]] = None
            response_body: Optional[Dict[str, Any]] = None
            try:
                lookup = provider.lookup(
                    mcc=mcc_i,
                    mnc=mnc_i,
                    lac=lac_i,
                    cell_id=cell_id_i,
                    radio_type=rt,
                    signal_strength=signal_strength,
                    timeout_s=10.0,
                )
                if not lookup:
                    continue

                lat, lon, accuracy_m = float(lookup.lat), float(lookup.lon), lookup.accuracy_m
                request_url = lookup.request_url
                request_body = lookup.request_body
                response_body = lookup.raw
                src = getattr(provider, "dataset_source", DatasetSource.OTHER)
                src_label = provider_name

                try:
                    TowerLookupLog.objects.create(
                        provider=provider_name,
                        mcc=mcc_i,
                        mnc=mnc_i,
                        lac=lac_i,
                        cell_id=cell_id_i,
                        pci=pci_i,
                        earfcn=earfcn_i,
                        success=True,
                        lat=lat,
                        lon=lon,
                        accuracy_m=float(accuracy_m) if accuracy_m is not None else None,
                        request_url=request_url,
                        request_body=request_body,
                        response_body=response_body,
                    )
                except Exception:
                    pass

                tower, created = CellTower.objects.get_or_create(
                    mcc=mcc_i,
                    mnc=mnc_i,
                    cell_id=cell_id_i,
                    lac=lac_i,
                    defaults={
                        "radio_type": rt,
                        "pci": pci_i,
                        "earfcn": earfcn_i,
                        "range_m": int(accuracy_m) if accuracy_m is not None else None,
                        "is_approximate": True,
                        "samples": None,
                        "lat": lat,
                        "lon": lon,
                        "tx_power": CellTower._meta.get_field("tx_power").default,
                        "antenna_azimuth": None,
                        "source": src,
                        "checked_count": 1,
                        "verified_count": 0,
                    },
                )
                if not created:
                    updated = False
                    if tower.source != DatasetSource.MANUAL:
                        if tower.lat != lat or tower.lon != lon:
                            tower.lat = lat
                            tower.lon = lon
                            updated = True
                    if tower.range_m is None and accuracy_m is not None:
                        tower.range_m = int(accuracy_m)
                        updated = True
                    tower.checked_count = (tower.checked_count or 0) + 1
                    if updated:
                        tower.source = src
                        tower.is_approximate = True
                        tower.save(
                            update_fields=[
                                "lat",
                                "lon",
                                "range_m",
                                "source",
                                "is_approximate",
                                "checked_count",
                                "updated_at",
                            ]
                        )
                    else:
                        tower.save(update_fields=["checked_count", "updated_at"])

                return ResolveResult(tower=tower, source=src_label)
            except Exception as exc:
                logger.exception("%s lookup failed: %s", provider_name, exc)
                try:
                    TowerLookupLog.objects.create(
                        provider=provider_name,
                        mcc=mcc_i,
                        mnc=mnc_i,
                        lac=lac_i,
                        cell_id=cell_id_i,
                        pci=pci_i,
                        earfcn=earfcn_i,
                        success=False,
                        request_url=request_url,
                        request_body=request_body,
                        response_body=response_body,
                        error=str(exc),
                    )
                except Exception:
                    pass
                continue

        return None
