from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cellular.serializers import (
    CalibrationRequestSerializer,
    CalibrationResponseSerializer,
    RefLossRequestSerializer,
    RefLossResponseSerializer,
)
from cellular.utils.geometry import earfcn_to_freq_mhz, estimate_ref_loss_from_earfcn


class CalibrationView(APIView):
    """محاسبه n_effective از یک نمونه ground-truth برای کالیبراسیون مدل"""

    @extend_schema(
        request=CalibrationRequestSerializer,
        responses=CalibrationResponseSerializer,
        description="Compute effective path-loss exponent `n` from ground-truth sample",
        summary="Calibration: compute n_effective",
        tags=["Calibration"],
    )
    def post(self, request):
        serializer = CalibrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # compute distance between tower and user
        import math

        R = 6371000.0
        lat1 = math.radians(data["tower_lat"])
        lon1 = math.radians(data["tower_lon"])
        lat2 = math.radians(data["user_lat"])
        lon2 = math.radians(data["user_lon"])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = R * c

        tx = data.get("tx")
        ref_loss = data.get("ref_loss")
        from math import log10

        tx_eff = tx if tx is not None else 40.0
        ref_eff = ref_loss if ref_loss is not None else 80.0
        if d <= 0:
            return Response(
                {"error": "distance between tower and user must be > 0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        n_effective = ((tx_eff - data["rsrp"]) - ref_eff) / (10.0 * log10(d))

        resp = {
            "n_effective": float(n_effective),
            "details": {
                "distance_m": f"{d:.2f}",
                "tx_used": str(tx_eff),
                "ref_loss_used": str(ref_eff),
            },
        }
        resp_ser = CalibrationResponseSerializer(resp)
        return Response(resp_ser.data, status=status.HTTP_200_OK)


class RefLossView(APIView):
    """Estimate REF_LOSS (reference path loss at 1m) from EARFCN or frequency."""

    @extend_schema(
        request=RefLossRequestSerializer,
        responses=RefLossResponseSerializer,
        description="Estimate REF_LOSS (dB) from `earfcn` or `freq_mhz`. Provide either field.",
        summary="Estimate Reference Path Loss",
        tags=["Calibration"],
    )
    def post(self, request, *args, **kwargs):
        serializer = RefLossRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        freq = data.get("freq_mhz")
        earfcn = data.get("earfcn")
        if not freq and earfcn:
            freq = earfcn

        if not freq:
            return Response(
                {"error": "Provide either earfcn or freq_mhz"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

