from __future__ import annotations

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView


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

