"""
Backward-compatible facade for tower resolution.

The codebase historically used `fetch_and_save_tower` from this module. The actual
implementation now lives in `cellular/services/tower_resolver.py` (DB-first with
optional external providers + upsert + logging).
"""

from __future__ import annotations

from cellular.services.tower_resolver import TowerResolver, _is_sentinel


def fetch_and_save_tower(
    mcc,
    mnc,
    cell_id,
    lac,
    pci=None,
    earfcn=None,
    reference_lat=None,
    reference_lon=None,
    *,
    allow_external: bool = False,
):
    resolver = TowerResolver(reference_lat=reference_lat, reference_lon=reference_lon)
    result = resolver.resolve(
        mcc=None if _is_sentinel(mcc) else int(mcc),
        mnc=None if _is_sentinel(mnc) else int(mnc),
        cell_id=None if _is_sentinel(cell_id) else int(cell_id),
        lac=None if lac is None or _is_sentinel(lac) else int(lac),
        pci=None if pci is None or _is_sentinel(pci) else int(pci),
        earfcn=None if earfcn is None or _is_sentinel(earfcn) else int(earfcn),
        allow_external=bool(allow_external),
    )
    return result.tower, result.source


__all__ = ["fetch_and_save_tower"]

