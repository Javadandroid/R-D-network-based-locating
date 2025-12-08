from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from cellular.utils.api_client import fetch_and_save_tower
from .models import CellTower
from .utils.geometry import calculate_distance, estimate_bearing, calculate_new_coordinates
from .serializers import (
    CellTowerSearchSerializer,
    CellTowerSerializer,
    LocateUserRequestSerializer,
    LocateUserResponseSerializer
)


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

        # یافتن anchor دکل (بهترین سیگنال)
        anchor_data = None
        for cell in cells_data:
            if cell.get('cellId') and cell.get('cellId') < 2147483647:
                anchor_data = cell
                break

        if not anchor_data:
            return Response(
                {"error": "No valid anchor cell found in request"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # جستجو در دیتابیس یا API
        tower_obj, source = fetch_and_save_tower(
            mcc=anchor_data['mcc'],
            mnc=anchor_data['mnc'],
            cell_id=anchor_data['cellId'],
            lac=anchor_data.get('lac'),
            pci=anchor_data.get('pci')
        )

        if not tower_obj:
            return Response(
                {
                    "error": "Tower not found",
                    "details": f"Could not find tower MCC={anchor_data['mcc']}, MNC={anchor_data['mnc']}, CID={anchor_data['cellId']}"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # الف) محاسبه شعاع (Radius) با Path Loss Model تهران
        rsrp = anchor_data['signalStrength']
        radius = calculate_distance(rsrp, tx_power=tower_obj.tx_power)

        # ب) محاسبه جهت (Bearing) از Cell ID
        bearing = estimate_bearing(tower_obj.cell_id)

        # ج) محاسبه موقعیت کاربر بر اساس دکل + شعاع + bearing
        # (نه موقعیت دکل)
        user_coords = calculate_new_coordinates(
            lat=tower_obj.lat,
            lon=tower_obj.lon,
            distance_meters=radius,
            bearing=bearing
        )
        
        final_lat = user_coords['lat']
        final_lon = user_coords['lon']

        response_data = {
            "location": {
                "lat": round(final_lat, 6),
                "lon": round(final_lon, 6),
                "google": f"{round(final_lat, 6)},{round(final_lon, 6)}"
            },
            "radius": round(radius, 2),
            "debug": {
                "source": source,
                "bearing_used": bearing,
                "signal": rsrp
            }
        }

        # ✅ Validate response
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
        towers = CellTower.objects.filter(**filters).values()

        # 4. Serialize و return
        response_serializer = CellTowerSerializer(towers, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)