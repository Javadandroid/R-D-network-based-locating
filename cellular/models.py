
from django.db import models
from django.db.models import Count, Q
from .choices import RadioType, DatasetSource

class CellTower(models.Model):
    # --- نوع سل تاور (Radio Type) ---
    radio_type = models.CharField(
        max_length=10,
        choices=RadioType.choices,
        default=RadioType.LTE,
        help_text="Type of Radio (e.g., GSM, LTE, NR)",
    )
    # ---   (Global Identity) ---
    mcc = models.IntegerField(help_text="Mobile Country Code (e.g., 432)")
    mnc = models.IntegerField(help_text="Mobile Network Code (e.g., 35)")
    lac = models.IntegerField(null=True, blank=True, help_text="Location Area Code / TAC")
    cell_id = models.BigIntegerField(null=True, blank=True, help_text="CID / ECI (Identity)")
    
    # ---information about the cell tower ---
    pci = models.IntegerField(null=True, blank=True, help_text="Physical Cell ID (0-503)")
    earfcn = models.IntegerField(null=True, blank=True, help_text="Frequency Channel")
    range_m = models.IntegerField(null=True, blank=True, help_text="Coverage range in meters", verbose_name="Tower Range")
    is_approximate = models.BooleanField(default=True,help_text="Indicates if the location is approximate")
    samples = models.IntegerField(null=True, blank=True,help_text="Total number of measurements assigned to the cell tower")

    # location information ---
    lat = models.FloatField()
    lon = models.FloatField()

    # --- signal information ---
    tx_power = models.IntegerField(
        default=42,  # مقدار پیش‌فرض اگر خالی باشد
        help_text="Transmission Power in dBm (Default: 40 for Urban Macro)"
    )
    antenna_azimuth = models.IntegerField(
        null=True,
        blank=True,
        help_text="Optional antenna azimuth (degrees 0-360) for this tower"
    )

    # --- system metadata ---
    source = models.CharField(
        max_length=20,
        choices=DatasetSource.choices,
        default=DatasetSource.OTHER,
        help_text="Primary dataset source for this entry",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    checked_count = models.PositiveIntegerField(default=0, help_text="Number of datasets that checked this tower")
    verified_count = models.PositiveIntegerField(default=0, help_text="Number of datasets that verified this tower")

    class Meta:
        unique_together = ('mcc', 'mnc', 'cell_id', 'lac')
        indexes = [
            models.Index(fields=['mcc', 'mnc', 'pci']), # برای جستجوی سریع همسایه‌ها
        ]

    def __str__(self):
        return f"{self.mcc}-{self.mnc}-{self.cell_id} (PCI: {self.pci})"


class TowerLookupLog(models.Model):
    """Minimal log of tower lookup attempts (external APIs)."""

    provider = models.CharField(max_length=20)
    mcc = models.IntegerField(null=True, blank=True)
    mnc = models.IntegerField(null=True, blank=True)
    lac = models.IntegerField(null=True, blank=True)
    cell_id = models.BigIntegerField(null=True, blank=True)
    pci = models.IntegerField(null=True, blank=True)
    earfcn = models.IntegerField(null=True, blank=True)

    success = models.BooleanField(default=False)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    accuracy_m = models.FloatField(null=True, blank=True)
    request_url = models.CharField(max_length=255, blank=True, default="")
    request_body = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
