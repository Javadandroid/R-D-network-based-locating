from __future__ import annotations

import os
import threading
from tempfile import NamedTemporaryFile

from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cellular.models import CellTower
from cellular.permissions import ImportApiKeyPermission
from cellular.serializers import (
    CellTowerBoundingBoxSerializer,
    CellTowerCsvUploadSerializer,
    CellTowerSearchSerializer,
    CellTowerMarkerSerializer,
    CellTowerSerializer,
)
from cellular.utils.import_jobs import create_job, get_job, update_job
from cellular.utils.importers import import_towers_from_csv


class CellTowerCreateView(generics.CreateAPIView):
    """ایجاد یک دکل سلولی جدید"""

    queryset = CellTower.objects.all()
    serializer_class = CellTowerSerializer

    @extend_schema(
        description="ایجاد یک دکل سلولی جدید در دیتابیس",
        summary="➕ Create New Cell Tower",
        tags=["Towers"],
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
        tags=["Towers"],
    )
    def post(self, request):
        search_serializer = CellTowerSearchSerializer(data=request.data)
        search_serializer.is_valid(raise_exception=True)
        data = search_serializer.validated_data

        filters = {
            "mcc": data["mcc"],
            "mnc": data["mnc"],
        }
        for field in ["lac", "pci", "cell_id"]:
            if field in data and data[field] is not None:
                filters[field] = data[field]

        towers = CellTower.objects.filter(**filters).order_by("-updated_at")[:500]
        response_serializer = CellTowerSerializer(towers, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


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
            serializer.validated_data["csv_file"],
            dataset_source=serializer.validated_data["dataset_source"],
            update_existing=serializer.validated_data["update_existing"],
        )
        return Response(stats, status=status.HTTP_201_CREATED)


class CellTowerBoundingBoxView(APIView):
    """Get towers within bounding box"""

    permission_classes = [AllowAny]

    @extend_schema(
        request=CellTowerBoundingBoxSerializer,
        responses={200: CellTowerMarkerSerializer(many=True)},
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

        towers_qs = (
            CellTower.objects.filter(
                lat__gte=data["min_lat"],
                lat__lte=data["max_lat"],
                lon__gte=data["min_lon"],
                lon__lte=data["max_lon"],
            )
            .only(
                "id",
                "radio_type",
                "mcc",
                "mnc",
                "lac",
                "cell_id",
                "pci",
                "earfcn",
                "lat",
                "lon",
                "tx_power",
                "source",
                "updated_at",
            )
            .order_by("-updated_at")[:limit]
        )

        return Response(CellTowerMarkerSerializer(towers_qs, many=True).data)


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
        description="Uploads CSV and starts import in background thread. Poll /api/v1/towers/import-status/<job_id>/ for progress.",
        tags=["Towers"],
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
        tags=["Towers"],
    )
    def get(self, request, job_id: str):
        job = get_job(job_id)
        if not job:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(job)
