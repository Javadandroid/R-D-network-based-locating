from rest_framework import serializers
from .models import CellTower
from .choices import DatasetSource


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
    """cell input data from user device"""
    cellId = serializers.IntegerField(
        help_text=" Cell ID"
    )
    mcc = serializers.IntegerField(
        help_text=" country code (e.g., 432 for Iran)"
    )
    mnc = serializers.IntegerField(
        help_text="operator code (e.g., 11 for Irancell"
    )
    signalStrength = serializers.IntegerField(
        help_text="Signal strength in dBm"
    )
    rsrq = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Reference Signal Received Quality (dB) if available",
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
    """user cell tower report request"""
    cells = CellInputSerializer(
        many=True,
        help_text="tower cell list detected by user device"
    )


class LocationResponseSerializer(serializers.Serializer):
    """calculated location"""
    lat = serializers.FloatField(
        help_text="Latitude"
    )
    lon = serializers.FloatField(
        help_text="Longitude"
    )
    
    google = serializers.CharField(
        help_text="google format(lat,lon)"
    )


class DebugInfoSerializer(serializers.Serializer):
    """debug information about each cell tower used in location calculation"""
    source = serializers.CharField(
        help_text="cell tower source (API/DB/WARD)"
    )
    bearing_used = serializers.FloatField(
        help_text=" calculated bearing (0-360 )",
        required=False,
        allow_null=True,
    )
    signal = serializers.IntegerField(
        help_text="signal strength used (dBm)",
        required=False,
        allow_null=True,
    )
    confidence = serializers.CharField(
        help_text="level of confidence (high/medium/low)",
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
    """location response serializer"""
    location = LocationResponseSerializer(
        help_text="calculated location"
    )
    radius = serializers.FloatField(
        help_text="uncertainty radius (meters)"
    )
    debug = DebugInfoSerializer(
        help_text="debug information about each cell tower used in location calculation"
    )


class CellTowerCsvUploadSerializer(serializers.Serializer):
    csv_file = serializers.FileField(help_text="CSV file containing cell tower records")
    dataset_source = serializers.ChoiceField(choices=DatasetSource.choices, help_text="Dataset source (e.g., MLS, OPENCELLID)")
    update_existing = serializers.BooleanField(
        required=False,
        default=True,
        help_text="If enabled, existing records will be updateds.",
    )


class CellTowerBoundingBoxSerializer(serializers.Serializer):
    min_lat = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        help_text="southest latitude of current map bounds",
    )
    max_lat = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        help_text="northernmost latitude of current map bounds",
    )
    min_lon = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        help_text="westmost longitude of current map bounds",
    )
    max_lon = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        help_text="eastmost longitude of current map bounds",
    )
    limit = serializers.IntegerField(
        min_value=1,
        max_value=200,
        default=50,
        help_text="maximum number of cell tower markers in the response (default 50, max 200)",
    )

    def validate(self, attrs):
        if attrs["min_lat"] >= attrs["max_lat"]:
            raise serializers.ValidationError("min_lat must be smaller than max_lat.")
        if attrs["min_lon"] >= attrs["max_lon"]:
            raise serializers.ValidationError("min_lon must be smaller than max_lon.")
        return attrs


class SnapshotLocateRequestSerializer(serializers.Serializer):
    endpoint = serializers.URLField(
        help_text="Snapshot API base endpoint. Example: https://api.example.com/snapshots"
    )
    snapshot_id = serializers.IntegerField(min_value=1, help_text="Snapshot ID to fetch")
    registered_only = serializers.BooleanField(
        required=False,
        default=True,
        help_text="If true, only use cells where `registered=true` in the snapshot",
    )
    max_cells = serializers.IntegerField(
        required=False,
        default=12,
        min_value=1,
        max_value=50,
        help_text="Max number of extracted cells to use in positioning",
    )
    include_anchors = serializers.BooleanField(
        required=False,
        default=True,
        help_text="If true, return tower anchor markers (best-effort) for visualization",
    )
    anchors_limit = serializers.IntegerField(
        required=False,
        default=15,
        min_value=0,
        max_value=200,
        help_text="Max number of anchor markers to return",
    )
    allow_external_neighbors = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If true, missing neighbor towers may be resolved via external APIs (paid).",
    )


class SnapshotLocateResponseSerializer(serializers.Serializer):
    snapshot_id = serializers.IntegerField()
    phone_location = serializers.DictField(required=False, allow_null=True)
    computed = LocateUserResponseSerializer()
    extracted_cells_count = serializers.IntegerField()
    snapshot_cells = serializers.ListField(child=serializers.DictField(), required=False)
    cells = serializers.ListField(child=serializers.DictField(), required=False)
    anchors = serializers.ListField(child=serializers.DictField(), required=False)
