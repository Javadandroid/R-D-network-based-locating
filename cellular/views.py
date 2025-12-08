from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from cellular.utils.api_client import fetch_and_save_tower
from .models import CellTower
from .utils.geometry import (
    calculate_distance,
    estimate_bearing,
    calculate_new_coordinates,
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
)
import logging

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
        **الگوریتم:**
        1. یافتن Anchor دکل (بهترین سیگنال و valid CID)
        2. جستجوی اطلاعات دکل در DB یا API
        3. محاسبه شعاع (Radius) با فرمول Path Loss
        4. محاسبه جهت (Bearing) از Cell ID
        5. اعمال Back Lobe برای سیگنال ضعیف
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

        # پاکسازی اولیه (حذف sentinel / ghost cells)
        cells = clean_cells(cells_data)
        if not cells:
            return Response({"error": "No valid cells after cleaning"}, status=status.HTTP_400_BAD_REQUEST)

        # اگر فقط یک سلول داریم -> single-tower logic
        if len(cells) == 1:
            c = cells[0]
            tower_obj, source = fetch_and_save_tower(
                mcc=c['mcc'],
                mnc=c['mnc'],
                cell_id=c['cellId'],
                lac=c.get('lac'),
                pci=c.get('pci')
            )
            rsrp = c.get('signalStrength')
            ta = c.get('timingAdvance')

            # prefer TA when available and valid
            ta_dist = distance_from_ta(ta)
            bearing_used = None
            confidence = 'medium'

            if ta_dist is not None:
                # Use TA-derived distance; position assumed near tower along unknown bearing
                radius = ta_dist
                final_lat = tower_obj.lat
                final_lon = tower_obj.lon
                confidence = 'high'
            else:
                # Near-field heuristic: very strong signals are trusted as close
                if rsrp is not None and rsrp > -70:
                    final_lat = tower_obj.lat
                    final_lon = tower_obj.lon
                    radius = 100.0
                    confidence = 'high'
                else:
                    # compute distance from path-loss
                    radius = calculate_distance(rsrp, tx_power=getattr(tower_obj, 'tx_power', None))
                    # use per-tower azimuth if available, else estimate from cell id
                    bearing_used = getattr(tower_obj, 'antenna_azimuth', None) if getattr(tower_obj, 'antenna_azimuth', None) is not None else estimate_bearing(tower_obj.cell_id)
                    coords = calculate_new_coordinates(tower_obj.lat, tower_obj.lon, radius, bearing_used)
                    final_lat = coords['lat']
                    final_lon = coords['lon']
                    confidence = 'low' if rsrp is None or rsrp <= -100 else 'medium'

            response_data = {
                "location": {"lat": round(final_lat, 6), "lon": round(final_lon, 6), "google": f"{round(final_lat,6)},{round(final_lon,6)}"},
                "radius": round(radius, 2),
                "debug": {"source": source, "bearing_used": bearing_used or 0.0, "signal": rsrp, "confidence": confidence}
            }
            response_serializer = LocateUserResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        # اگر دو سلول داریم -> weighted centroid
        if len(cells) == 2:
            towers_info = []
            for c in cells:
                tower_obj, source = fetch_and_save_tower(
                    mcc=c['mcc'], mnc=c['mnc'], cell_id=c['cellId'], lac=c.get('lac'), pci=c.get('pci')
                )
                towers_info.append({'lat': tower_obj.lat, 'lon': tower_obj.lon, 'rsrp': c['signalStrength']})

            centroid = weighted_centroid(towers_info)
            if centroid is None:
                return Response({"error": "Unable to compute centroid"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            response_data = {
                "location": {"lat": round(centroid['lat'], 6), "lon": round(centroid['lon'], 6), "google": f"{round(centroid['lat'],6)},{round(centroid['lon'],6)}"},
                "radius":  max(50.0, round(min([calculate_distance(c['signalStrength']) for c in cells]), 2)),
                "debug": {"source": "COMPOSITE", "bearing_used": None, "signal": None}
            }
            response_serializer = LocateUserResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        # سه یا بیشتر -> تلاش برای Trilateration با 3 قوی‌ترین سیگنال
        # مرتب‌سازی بر اساس قدرت سیگنال (قوی‌تر یعنی عدد بزرگتر - نزدیک به 0)
        sorted_cells = sorted(cells, key=lambda x: x['signalStrength'], reverse=True)
        top3 = sorted_cells[:3]
        tower_objs = []
        for c in top3:
            tower_obj, source = fetch_and_save_tower(
                mcc=c['mcc'], mnc=c['mnc'], cell_id=c['cellId'], lac=c.get('lac'), pci=c.get('pci')
            )
            radius = calculate_distance(c['signalStrength'], tx_power=getattr(tower_obj, 'tx_power', None))
            tower_objs.append({'lat': tower_obj.lat, 'lon': tower_obj.lon, 'radius': radius, 'rsrp': c['signalStrength']})

        trilat = trilaterate_three(tower_objs[0], tower_objs[1], tower_objs[2])
        if trilat:
            final_lat, final_lon = trilat
            radius = min([t['radius'] for t in tower_objs])
            response_data = {
                "location": {"lat": round(final_lat, 6), "lon": round(final_lon, 6), "google": f"{round(final_lat,6)},{round(final_lon,6)}"},
                "radius": round(radius, 2),
                "debug": {"source": "TRILATERATION", "bearing_used": None, "signal": None}
            }
            response_serializer = LocateUserResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        # fallback: weighted centroid for all
        towers_info = []
        for c in cells:
            tower_obj, source = fetch_and_save_tower(mcc=c['mcc'], mnc=c['mnc'], cell_id=c['cellId'], lac=c.get('lac'), pci=c.get('pci'))
            towers_info.append({'lat': tower_obj.lat, 'lon': tower_obj.lon, 'rsrp': c['signalStrength']})

        centroid = weighted_centroid(towers_info)
        if centroid is None:
            return Response({"error": "Unable to compute location"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = {
            "location": {"lat": round(centroid['lat'], 6), "lon": round(centroid['lon'], 6), "google": f"{round(centroid['lat'],6)},{round(centroid['lon'],6)}"},
            "radius": round(max([calculate_distance(c['signalStrength']) for c in cells]), 2),
            "debug": {"source": "FALLBACK_CENTROID", "bearing_used": None, "signal": None}
        }
        response_serializer = LocateUserResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    
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