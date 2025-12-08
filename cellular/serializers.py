from rest_framework import serializers
from .models import CellTower


class CellTowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CellTower
        fields = '__all__'


class CellTowerSearchSerializer(serializers.Serializer):
    mcc = serializers.IntegerField(help_text="Mobile Country Code")
    mnc = serializers.IntegerField(help_text="Mobile Network Code")
    lac = serializers.IntegerField(required=False, help_text="Location Area Code")
    pci = serializers.IntegerField(required=False, help_text="Physical Cell ID")
    cell_id = serializers.IntegerField(required=False, help_text="Global Cell ID")


# ==================== LocateUser Serializers ====================

class CellInputSerializer(serializers.Serializer):
    """یک سلول دریافت شده از کاربر (Android/Modem)"""
    cellId = serializers.IntegerField(
        help_text="شناسه سلول (CID/ECI) - شناسه یکتا سلول"
    )
    mcc = serializers.IntegerField(
        help_text="کد کشور (432 = ایران)"
    )
    mnc = serializers.IntegerField(
        help_text="کد اپراتور (35=MCI, 20=Hamrah, 32=Rightel)"
    )
    signalStrength = serializers.IntegerField(
        help_text="قدرت سیگنال RSRP (dBm) - منفی است"
    )
    timingAdvance = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Timing Advance (TA) if available"
    )
    lac = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Location Area Code / TAC"
    )
    pci = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Physical Cell ID (0-503)"
    )


class LocateUserRequestSerializer(serializers.Serializer):
    """درخواست موقعیت‌یابی - لیست دکل‌های دریافت شده"""
    cells = CellInputSerializer(
        many=True,
        help_text="لیست دکل‌های دریافت شده از موبایل"
    )


class LocationResponseSerializer(serializers.Serializer):
    """موقعیت محاسبه شده"""
    lat = serializers.FloatField(
        help_text="عرض جغرافیایی (Latitude)"
    )
    lon = serializers.FloatField(
        help_text="طول جغرافیایی (Longitude)"
    )
    
    google = serializers.CharField(
        help_text="فرمت مختصات برای گوگل مپس (lat,lon)"
    )


class DebugInfoSerializer(serializers.Serializer):
    """اطلاعات debug و جزئیات محاسبه"""
    source = serializers.CharField(
        help_text="منبع داده دکل (API/DB/WARD)"
    )
    bearing_used = serializers.FloatField(
        help_text="جهت محاسبه شده (0-360 درجه)"
    )
    signal = serializers.IntegerField(
        help_text="قدرت سیگنال استفاده شده (dBm)"
    )
    confidence = serializers.CharField(
        help_text="سطح اعتماد (high/medium/low)",
        required=False,
        allow_null=True
    )


class CalibrationRequestSerializer(serializers.Serializer):
    tower_lat = serializers.FloatField()
    tower_lon = serializers.FloatField()
    rsrp = serializers.IntegerField()
    user_lat = serializers.FloatField()
    user_lon = serializers.FloatField()
    tx = serializers.IntegerField(required=False, allow_null=True)
    ref_loss = serializers.FloatField(required=False, allow_null=True)


class CalibrationResponseSerializer(serializers.Serializer):
    n_effective = serializers.FloatField()
    details = serializers.DictField(child=serializers.CharField(), required=False)


class RefLossRequestSerializer(serializers.Serializer):
    earfcn = serializers.IntegerField(required=False, allow_null=True)
    freq_mhz = serializers.FloatField(required=False, allow_null=True)
    gt_dbi = serializers.FloatField(required=False, default=15.0)
    gr_dbi = serializers.FloatField(required=False, default=0.0)
    system_losses_db = serializers.FloatField(required=False, default=3.0)


class RefLossResponseSerializer(serializers.Serializer):
    freq_mhz = serializers.FloatField()
    ref_loss_db = serializers.FloatField()
    details = serializers.DictField(child=serializers.CharField(), required=False)


class LocateUserResponseSerializer(serializers.Serializer):
    """پاسخ موقعیت‌یابی"""
    location = LocationResponseSerializer(
        help_text="موقعیت نهایی کاربر"
    )
    radius = serializers.FloatField(
        help_text="شعاع عدم‌قطعیت (متر)"
    )
    debug = DebugInfoSerializer(
        help_text="اطلاعات debug"
    )