from django.db import models
from .choices import RadioType

class CellTower(models.Model):
    # --- نوع سل تاور (Radio Type) ---
    radio_type = models.CharField(
        max_length=10,
        choices=RadioType.choices,
        default=RadioType.LTE,
        help_text="Type of Radio (e.g., GSM, LTE, NR)"
    )
    # --- شناسه یکتا (Global Identity) ---
    mcc = models.IntegerField(help_text="Mobile Country Code (e.g., 432)")
    mnc = models.IntegerField(help_text="Mobile Network Code (e.g., 35)")
    lac = models.IntegerField(null=True, blank=True, help_text="Location Area Code / TAC")
    cell_id = models.BigIntegerField(null=True, blank=True, help_text="CID / ECI (Identity)")
    
    # --- شناسه فیزیکی (برای دکل‌های همسایه) ---
    pci = models.IntegerField(null=True, blank=True, help_text="Physical Cell ID (0-503)")
    earfcn = models.IntegerField(null=True, blank=True, help_text="Frequency Channel")

    # --- موقعیت مکانی (هدف نهایی) ---
    lat = models.FloatField()
    lon = models.FloatField()
    
    # --- اطلاعات سیگنال (اختیاری - میانگین قدرت دیده شده) ---
    tx_power = models.IntegerField(
        default=40,  # مقدار پیش‌فرض اگر خالی باشد
        help_text="Transmission Power in dBm (Default: 40 for Urban Macro)"
    )
    antenna_azimuth = models.IntegerField(
        null=True,
        blank=True,
        help_text="Optional antenna azimuth (degrees 0-360) for this tower"
    )
    
    # --- متادیتای سیستم ---
    SOURCE_CHOICES = [
        ('MANUAL', 'Manual Entry'),
        ('API', 'Fetched from External API'),
        ('WARD', 'War Driving Collection'),
    ]
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='API')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mcc', 'mnc', 'cell_id', 'lac')
        indexes = [
            models.Index(fields=['mcc', 'mnc', 'pci']), # برای جستجوی سریع همسایه‌ها
        ]

    def __str__(self):
        return f"{self.mcc}-{self.mnc}-{self.cell_id} (PCI: {self.pci})"