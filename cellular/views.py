from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.authentication import BaseAuthentication
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from cellular.utils.api_client import fetch_and_save_tower
from .models import CellTower
from .utils.geometry import (
    calculate_distance,
    estimate_bearing,
    calculate_new_coordinates,
    trilaterate_two_towers,
    weighted_centroid,
    trilaterate_three,
    distance_from_ta,
    earfcn_to_freq_mhz,
    estimate_ref_loss_from_earfcn,
)
from .utils.cleaners import clean_cells
from .serializers import (
    CellTowerSearchSerializer,
    CellTowerSerializer,
    LocateUserRequestSerializer,
    LocateUserResponseSerializer,
    CalibrationRequestSerializer,
    CalibrationResponseSerializer,
    RefLossRequestSerializer,
    RefLossResponseSerializer,
    CellTowerCsvUploadSerializer,
    CellTowerBoundingBoxSerializer,
    SnapshotLocateRequestSerializer,
    SnapshotLocateResponseSerializer,
)
from .utils.importers import import_towers_from_csv
from .utils.import_jobs import create_job, get_job, update_job
from cellular.services.locator import locate_cells, build_anchor_markers
from cellular.utils.net import is_allowed_snapshot_url
from cellular.utils.snapshots import extract_cells_from_snapshot, extract_phone_location, infer_default_mcc_mnc
from cellular.permissions import ImportApiKeyPermission
from urllib.parse import urljoin
import requests
import logging
from django.conf import settings
from django.db import connection
import threading
from tempfile import NamedTemporaryFile
import os

logger = logging.getLogger(__name__)


class LocateUserView(APIView):


    @extend_schema(
        request=LocateUserRequestSerializer,
        responses=LocateUserResponseSerializer,
        description="محاسبه موقعیت کاربر بر اساس سلول‌های دریافت شده",
        summary="Locate User by Cell Towers",
        tags=["Positioning"]
    )
    def post(self, request):
        """
        **Algorithm:**
        1. Find Anchor Cell Towers in DB or via API
        2. Search for tower details in DB or API
        3. Calculate radius (meters) using Path Loss formula
        4. Calculate bearing from Cell ID
        5. Apply Back Lobe for weak signals
        """
        # ✅ Validation with serializer
        serializer = LocateUserRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request format", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # دریافت داده‌های validated
        cells_data = serializer.validated_data.get('cells', [])

        try:
            response_data = locate_cells(cells_data)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa
            logger.exception("Locate error: %s", exc)
            return Response({"error": "Unable to compute location"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(LocateUserResponseSerializer(response_data).data, status=status.HTTP_200_OK)

    
class CellTowerCreateView(generics.CreateAPIView):
    """ایجاد یک دکل سلولی جدید"""
    queryset = CellTower.objects.all()
    serializer_class = CellTowerSerializer
    
    @extend_schema(
        description="ایجاد یک دکل سلولی جدید در دیتابیس",
        summary="➕ Create New Cell Tower",
        tags=["Towers"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    
class CellTowerSearchView(APIView):
    """جستجوی دکل‌ها بر اساس MCC، MNC، LAC، PCI"""
    
    @extend_schema(
        request=CellTowerSearchSerializer,
        responses={200: CellTowerSerializer(many=True)},
        description="جستجوی دکل‌های سلولی بر اساس شناسه‌ها",
        summary="🔍 Search Cell Towers",
        tags=["Towers"]
    )
    def post(self, request):
        """
        **پارامترهای جستجو:**
        - mcc: کد کشور (الزامی)
        - mnc: کد اپراتور (الزامی)
        - lac: Location Area Code (اختیاری)
        - pci: Physical Cell ID (اختیاری)
        - cell_id: Cell ID (اختیاری)
        """
        # 1. اعتبارسنجی داده‌های ورودی
        search_serializer = CellTowerSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)
        data = search_serializer.validated_data

        # 2. ساخت فیلترهای جستجو (بهینه‌شده)
        filters = {
            'mcc': data['mcc'],
            'mnc': data['mnc'],
        }
        
        # اضافه کردن فیلترهای اختیاری تنها اگر موجود باشند
        for field in ['lac', 'pci', 'cell_id']:
            if field in data and data[field] is not None:
                filters[field] = data[field]

        # 3. جستجو در دیتابیس (با select_related برای بهترین پرفورمنس)
        towers = CellTower.objects.filter(**filters)

        # 4. Serialize و return
        response_serializer = CellTowerSerializer(towers, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)



class CalibrationView(APIView):
    """محاسبه n_effective از یک نمونه ground-truth برای کالیبراسیون مدل"""

    @extend_schema(
        request=CalibrationRequestSerializer,
        responses=CalibrationResponseSerializer,
        description="Compute effective path-loss exponent `n` from ground-truth sample",
        summary="Calibration: compute n_effective",
        tags=["Calibration"]
    )
    def post(self, request):
        serializer = CalibrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # compute distance between tower and user
        import math
        R = 6371000.0
        lat1 = math.radians(data['tower_lat'])
        lon1 = math.radians(data['tower_lon'])
        lat2 = math.radians(data['user_lat'])
        lon2 = math.radians(data['user_lon'])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c

        tx = data.get('tx')
        ref_loss = data.get('ref_loss')
        from math import log10
        tx_eff = tx if tx is not None else 40.0
        ref_eff = ref_loss if ref_loss is not None else 80.0
        # avoid log10(0)
        if d <= 0:
            return Response({"error": "distance between tower and user must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

        n_effective = ((tx_eff - data['rsrp']) - ref_eff) / (10.0 * log10(d))

        resp = {"n_effective": float(n_effective), "details": {"distance_m": f"{d:.2f}", "tx_used": str(tx_eff), "ref_loss_used": str(ref_eff)}}
        resp_ser = CalibrationResponseSerializer(resp)
        return Response(resp_ser.data, status=status.HTTP_200_OK)


class RefLossView(APIView):
    """Estimate REF_LOSS (reference path loss at 1m) from EARFCN or frequency.

    Accepts `earfcn` or `freq_mhz` and optional antenna gains and system losses.
    Returns an estimated `ref_loss_db` to use in the path-loss formula.
    """

    @extend_schema(
        request=RefLossRequestSerializer,
        responses=RefLossResponseSerializer,
        description="Estimate REF_LOSS (dB) from `earfcn` or `freq_mhz`. Provide either field.",
        summary="Estimate Reference Path Loss",
        tags=["Calibration"]
    )
    def post(self, request, *args, **kwargs):
        """POST: body should be JSON matching RefLossRequestSerializer"""
        serializer = RefLossRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        freq = data.get("freq_mhz")
        earfcn = data.get("earfcn")
        # if freq not provided, try to derive from earfcn
        if not freq and earfcn:
            # earfcn may be int or string; helper will handle common cases
            freq = earfcn

        if not freq:
            return Response({"error": "Provide either earfcn or freq_mhz"}, status=status.HTTP_400_BAD_REQUEST)

        gt = data.get("gt_dbi", 15.0)
        gr = data.get("gr_dbi", 0.0)
        sys_losses = data.get("system_losses_db", 3.0)

        ref_loss_db = estimate_ref_loss_from_earfcn(freq, gt_dbi=gt, gr_dbi=gr, system_losses_db=sys_losses)

        resp = {
            "freq_mhz": float(earfcn_to_freq_mhz(freq) if isinstance(freq, (int, float)) else float(freq)),
            "ref_loss_db": float(ref_loss_db) if ref_loss_db is not None else None,
            "details": {"gt_dbi": str(gt), "gr_dbi": str(gr), "system_losses_db": str(sys_losses)},
        }

        return Response(RefLossResponseSerializer(resp).data)


class CellTowerBulkUploadView(APIView):
    """Upload from csv"""

    parser_classes = [MultiPartParser]
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [ImportApiKeyPermission]

    @extend_schema(
        request=CellTowerCsvUploadSerializer,
        responses={201: CellTowerCsvUploadSerializer},
        summary="⬆️ Import towers from CSV",
        description="Upload a CSV file.",
        tags=["Towers"],
    )
    def post(self, request, *args, **kwargs):
        serializer = CellTowerCsvUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stats = import_towers_from_csv(
            serializer.validated_data['csv_file'],
            dataset_source=serializer.validated_data['dataset_source'],
            update_existing=serializer.validated_data['update_existing'],
        )
        return Response(stats, status=status.HTTP_201_CREATED)


class CellTowerBoundingBoxView(APIView):
    """Get towers within bounding box"""

    permission_classes = [AllowAny]

    @extend_schema(
        request=CellTowerBoundingBoxSerializer,
        responses={200: CellTowerSerializer(many=True)},
        summary="📡 Towers within map bounds",
        description="Get towers within the specified bounding box. Maximum number of responses is configurable.",
        tags=["Towers"],
    )
    def post(self, request, *args, **kwargs):
        serializer = CellTowerBoundingBoxSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        limit = min(
            data.get("limit", 50),
            getattr(settings, "MAX_TOWERS_PER_REQUEST", 50),
        )

        towers_qs = CellTower.objects.filter(
            lat__gte=data["min_lat"],
            lat__lte=data["max_lat"],
            lon__gte=data["min_lon"],
            lon__lte=data["max_lon"],
        ).order_by("-updated_at")[:limit]

        return Response(CellTowerSerializer(towers_qs, many=True).data)


def _run_import_job(job_id: str, file_path: str, dataset_source: str, update_existing: bool) -> None:
    try:
        with open(file_path, "rb") as f:
            import_towers_from_csv(
                f,
                dataset_source=dataset_source,
                update_existing=update_existing,
                job_id=job_id,
            )
    except Exception as exc:  # noqa
        update_job(job_id, status="FAILED", error=str(exc))
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


class ImportStartView(APIView):
    """Start async-ish CSV import (thread-based) with progress polling."""

    parser_classes = [MultiPartParser]
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [ImportApiKeyPermission]

    @extend_schema(
        request=CellTowerCsvUploadSerializer,
        responses={200: {"type": "object", "properties": {"job_id": {"type": "string"}}}},
        summary="Start CSV import",
        description="Uploads CSV and starts import in background thread. Poll /api/towers/import-status/<job_id>/ for progress.",
    )
    def post(self, request, *args, **kwargs):
        serializer = CellTowerCsvUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["csv_file"]
        dataset_source = serializer.validated_data["dataset_source"]
        update_existing = serializer.validated_data["update_existing"]

        tmp = NamedTemporaryFile(delete=False, suffix=".csv")
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
        tmp.close()

        job_id = create_job()
        thread = threading.Thread(
            target=_run_import_job,
            args=(job_id, tmp_path, dataset_source, update_existing),
            daemon=True,
        )
        thread.start()

        return Response({"job_id": job_id, "status": "IN_PROGRESS"}, status=status.HTTP_200_OK)


class ImportStatusView(APIView):
    """Poll import job status."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Import job status",
        description="Returns job progress and recent updates",
        responses={
            200: inline_serializer(
                name="ImportJobStatus",
                fields={
                    "id": serializers.CharField(),
                    "status": serializers.CharField(),
                    "total_rows": serializers.IntegerField(),
                    "processed_rows": serializers.IntegerField(),
                    "errors": serializers.ListField(child=serializers.CharField(), required=False),
                    "last_updates": serializers.ListField(child=serializers.DictField(), required=False),
                },
            ),
            404: inline_serializer(
                name="ImportJobNotFound",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
    def get(self, request, job_id: str):
        job = get_job(job_id)
        if not job:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(job)


class SnapshotLocateView(APIView):
    """
    Fetch a snapshot JSON from an external API endpoint, extract raw_data.cellTowerInfo,
    run the same locate algorithm, and return:
    - phone (ground-truth) location from snapshot.location.selected_*
    - computed location from our algorithm
    """

    permission_classes = [AllowAny]

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
            return Response({"error": "Failed to fetch snapshot"}, status=status.HTTP_502_BAD_GATEWAY)

        phone_loc = extract_phone_location(snapshot)
        ref_lat = phone_loc.get("lat") if phone_loc else None
        ref_lon = phone_loc.get("lng") if phone_loc else None
        default_mcc, default_mnc = infer_default_mcc_mnc(snapshot)
        allow_external_neighbors = bool(data.get("allow_external_neighbors", False)) or bool(
            getattr(settings, "ALLOW_EXTERNAL_NEIGHBOR_LOOKUP", False)
        )

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
                    tower_obj, tower_source = fetch_and_save_tower(
                        mcc=int(mcc),
                        mnc=int(mnc),
                        cell_id=int(cell_id),
                        lac=int(lac) if lac is not None else None,
                        pci=int(pci) if pci is not None else None,
                        earfcn=int(earfcn) if earfcn is not None else None,
                        reference_lat=ref_lat,
                        reference_lon=ref_lon,
                        allow_external=bool(allow_external_neighbors and not registered),
                    )
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
            return Response({"error": "No usable cells found in snapshot"}, status=status.HTTP_400_BAD_REQUEST)

        # Build a diagnostic list: cleaned cells + whether tower exists in our DB.
        cleaned_cells = clean_cells(cells)
        cells_for_table = []

        towers_found_cells = []
        for c in cleaned_cells:
            tower_obj, source = fetch_and_save_tower(
                mcc=c["mcc"],
                mnc=c["mnc"],
                cell_id=c["cellId"],
                lac=c.get("lac"),
                pci=c.get("pci"),
                earfcn=c.get("earfcn"),
                reference_lat=ref_lat,
                reference_lon=ref_lon,
                allow_external=True,
            )
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
            return Response({"error": "No valid cells after cleaning"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            computed = locate_cells(
                cleaned_cells,
                reference_lat=ref_lat,
                reference_lon=ref_lon,
                allow_external_neighbors=allow_external_neighbors,
                allow_external_serving=True,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa
            logger.exception("Snapshot locate error: %s", exc)
            return Response({"error": "Unable to compute location"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                allow_external_neighbors=allow_external_neighbors,
                allow_external_serving=True,
            )

        return Response(SnapshotLocateResponseSerializer(response_data).data, status=status.HTTP_200_OK)


class DbInfoView(APIView):
    """
    Lightweight diagnostic endpoint to confirm which DB backend is active.
    Intended for local debugging; in production restrict access.
    """

    permission_classes = [AllowAny] if getattr(settings, "DEBUG", False) else [IsAdminUser]

    @extend_schema(
        summary="DB info (debug)",
        description="Returns the active Django DB vendor/engine/name/host/port to confirm whether PostgreSQL is being used.",
        responses={
            200: inline_serializer(
                name="DbInfo",
                fields={
                    "vendor": serializers.CharField(),
                    "engine": serializers.CharField(allow_null=True, required=False),
                    "name": serializers.CharField(allow_null=True, required=False),
                    "host": serializers.CharField(allow_null=True, required=False),
                    "port": serializers.CharField(allow_null=True, required=False),
                },
            )
        },
        tags=["System"],
    )
    def get(self, request, *args, **kwargs):
        cfg = connection.settings_dict
        return Response(
            {
                "vendor": connection.vendor,
                "engine": cfg.get("ENGINE"),
                "name": cfg.get("NAME"),
                "host": cfg.get("HOST"),
                "port": cfg.get("PORT"),
            }
        )
