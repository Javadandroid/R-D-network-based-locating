from __future__ import annotations

import logging
from urllib.parse import urljoin

import requests
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cellular.services.locator import build_anchor_markers, locate_cells
from cellular.services.tower_resolver import TowerResolver
from cellular.serializers import (
    LocateUserRequestSerializer,
    LocateUserResponseSerializer,
    SnapshotLocateRequestSerializer,
    SnapshotLocateResponseSerializer,
)
from cellular.utils.cleaners import clean_cells
from cellular.utils.net import is_allowed_snapshot_url
from cellular.utils.snapshots import (
    extract_cells_from_snapshot,
    extract_phone_location,
    infer_default_mcc_mnc,
)

logger = logging.getLogger(__name__)

def _guess_radio_type(cell_type: object) -> str | None:
    s = str(cell_type or "").lower()
    if not s:
        return None
    if "nr" in s or "5g" in s:
        return "nr"
    if "lte" in s or "4g" in s:
        return "lte"
    if "wcdma" in s or "umts" in s or "3g" in s:
        return "umts"
    if "gsm" in s or "2g" in s:
        return "gsm"
    return None


class LocateUserView(APIView):
    @extend_schema(
        request=LocateUserRequestSerializer,
        responses=LocateUserResponseSerializer,
        description="محاسبه موقعیت کاربر بر اساس سلول‌های دریافت شده",
        summary="Locate User by Cell Towers",
        tags=["Positioning"],
    )
    def post(self, request):
        serializer = LocateUserRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request format", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cells_data = serializer.validated_data.get("cells", [])

        try:
            response_data = locate_cells(cells_data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa
            logger.exception("Locate error: %s", exc)
            return Response(
                {"error": "Unable to compute location"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            LocateUserResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )


class SnapshotLocateView(APIView):
    """
    Fetch a snapshot JSON from an external API endpoint, extract raw_data.cellTowerInfo,
    run the same locate algorithm, and return:
    - phone (ground-truth) location from snapshot.location.selected_*
    - computed location from our algorithm
    """

    permission_classes = [AllowAny]
    # Public endpoint (no session auth). Disable SessionAuthentication to avoid CSRF 403
    # when the frontend sends cookies (credentials: "include").
    authentication_classes: list[type[BaseAuthentication]] = []

    @extend_schema(
        request=SnapshotLocateRequestSerializer,
        responses=SnapshotLocateResponseSerializer,
        summary="Locate from external snapshot",
        description="Fetch snapshot JSON (allowlisted hosts), extract cells from raw_data.cellTowerInfo.allCellInfo and run locate.",
        tags=["Positioning"],
    )
    def post(self, request, *args, **kwargs):
        ser = SnapshotLocateRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        endpoint = data["endpoint"].rstrip("/") + "/"
        snapshot_id = data["snapshot_id"]
        url = urljoin(endpoint, f"{snapshot_id}/")

        allowed_hosts = getattr(settings, "SNAPSHOT_ALLOWED_HOSTS", [])
        if not is_allowed_snapshot_url(url, allowed_hosts):
            return Response(
                {
                    "error": "Snapshot URL host is not allowed. Configure SNAPSHOT_ALLOWED_HOSTS in environment.",
                    "host": url,
                    "allowed_hosts": allowed_hosts,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resp = requests.get(url, timeout=10, allow_redirects=False)
            resp.raise_for_status()
            snapshot = resp.json()
        except Exception as exc:  # noqa
            logger.exception("Snapshot fetch failed: %s", exc)
            return Response(
                {"error": "Failed to fetch snapshot"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        phone_loc = extract_phone_location(snapshot)
        ref_lat = phone_loc.get("lat") if phone_loc else None
        ref_lon = phone_loc.get("lng") if phone_loc else None
        default_mcc, default_mnc = infer_default_mcc_mnc(snapshot)
        allow_external_neighbors = bool(data.get("allow_external_neighbors", False)) or bool(
            getattr(settings, "ALLOW_EXTERNAL_NEIGHBOR_LOOKUP", False)
        )
        resolver = TowerResolver(reference_lat=ref_lat, reference_lon=ref_lon)

        # Table data: raw snapshot cell records enriched with DB lookup (if exists)
        raw = snapshot.get("raw_data") or {}
        cti = raw.get("cellTowerInfo") or {}
        all_cell_info = cti.get("allCellInfo") or []
        snapshot_cells_for_table = []
        for idx, item in enumerate(all_cell_info[:500]):  # safety cap
            if not isinstance(item, dict):
                continue

            cell_type = item.get("type")
            mcc = item.get("mcc")
            mnc = item.get("mnc")

            # LTE uses `ci`/`tac`, UMTS uses `cid`/`lac`
            cell_id = item.get("ci", item.get("cid"))
            lac = item.get("tac", item.get("lac"))
            pci = item.get("pci", item.get("psc"))
            earfcn = item.get("earfcn", item.get("uarfcn", item.get("arfcn")))
            rsrp = item.get("rsrp", item.get("dbm"))
            rsrq = item.get("rsrq")
            registered = item.get("registered")

            # Infer MCC/MNC for neighbor cells with sentinel values using simOperator.
            if mcc in (None, 2147483647) and default_mcc is not None:
                mcc = default_mcc
            if mnc in (None, 2147483647) and default_mnc is not None:
                mnc = default_mnc

            tower_obj = None
            tower_source = None
            try:
                if mcc is not None and mnc is not None and cell_id is not None:
                    res = resolver.resolve(
                        radio_type=_guess_radio_type(cell_type),
                        mcc=int(mcc),
                        mnc=int(mnc),
                        cell_id=int(cell_id),
                        lac=int(lac) if lac is not None else None,
                        pci=int(pci) if pci is not None else None,
                        earfcn=int(earfcn) if earfcn is not None else None,
                        signal_strength=int(rsrp) if rsrp is not None else None,
                        allow_external=bool(allow_external_neighbors and not registered),
                    )
                    tower_obj, tower_source = res.tower, res.source
            except Exception:
                tower_obj = None
                tower_source = None

            snapshot_cells_for_table.append(
                {
                    "idx": idx,
                    "type": cell_type,
                    "registered": registered,
                    "mcc": mcc,
                    "mnc": mnc,
                    "lac": lac,
                    "cell_id": cell_id,
                    "pci": pci,
                    "earfcn": earfcn,
                    "rsrp": rsrp,
                    "rsrq": rsrq,
                    "dbm": item.get("dbm"),
                    "alphaLong": item.get("alphaLong"),
                    "alphaShort": item.get("alphaShort"),
                    "bandwidth": item.get("bandwidth"),
                    "level": item.get("level"),
                    "tower_found": tower_obj is not None,
                    "tower_lat": getattr(tower_obj, "lat", None) if tower_obj is not None else None,
                    "tower_lon": getattr(tower_obj, "lon", None) if tower_obj is not None else None,
                    "tower_source": tower_source,
                }
            )

        cells = extract_cells_from_snapshot(
            snapshot,
            registered_only=data.get("registered_only", True),
            max_cells=data.get("max_cells", 12),
        )
        if not cells:
            return Response(
                {"error": "No usable cells found in snapshot"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cleaned_cells = clean_cells(cells)
        cells_for_table = []

        towers_found_cells = []
        for c in cleaned_cells:
            res = resolver.resolve(
                radio_type=c.get("radio_type"),
                mcc=c["mcc"],
                mnc=c["mnc"],
                cell_id=c["cellId"],
                lac=c.get("lac"),
                pci=c.get("pci"),
                earfcn=c.get("earfcn"),
                signal_strength=c.get("signalStrength"),
                allow_external=True,
            )
            tower_obj, source = res.tower, res.source
            tower_found = tower_obj is not None
            if tower_found:
                towers_found_cells.append(c)
            cells_for_table.append(
                {
                    "radio_type": c.get("radio_type"),
                    "mcc": c.get("mcc"),
                    "mnc": c.get("mnc"),
                    "lac": c.get("lac"),
                    "cell_id": c.get("cellId"),
                    "pci": c.get("pci"),
                    "earfcn": c.get("earfcn"),
                    "signalStrength": c.get("signalStrength"),
                    "timingAdvance": c.get("timingAdvance"),
                    "registered": c.get("registered"),
                    "tower_found": tower_found,
                    "tower_lat": getattr(tower_obj, "lat", None) if tower_found else None,
                    "tower_lon": getattr(tower_obj, "lon", None) if tower_found else None,
                    "tower_source": source,
                }
            )

        if not cleaned_cells:
            return Response(
                {"error": "No valid cells after cleaning"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            computed = locate_cells(
                cleaned_cells,
                reference_lat=ref_lat,
                reference_lon=ref_lon,
                resolver=resolver,
                allow_external_neighbors=allow_external_neighbors,
                allow_external_serving=True,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa
            logger.exception("Snapshot locate error: %s", exc)
            return Response(
                {"error": "Unable to compute location"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {
            "snapshot_id": snapshot_id,
            "phone_location": extract_phone_location(snapshot),
            "computed": computed,
            "extracted_cells_count": len(cells),
            "snapshot_cells": snapshot_cells_for_table,
            "cells": cells_for_table,
        }

        if data.get("include_anchors", True):
            response_data["anchors"] = build_anchor_markers(
                cleaned_cells,
                limit=data.get("anchors_limit", 15),
                reference_lat=ref_lat,
                reference_lon=ref_lon,
                resolver=resolver,
                allow_external_neighbors=allow_external_neighbors,
                allow_external_serving=True,
            )

        return Response(
            SnapshotLocateResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )
