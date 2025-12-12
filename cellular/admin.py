from django.contrib import admin
from .models import CellTower

# Register your models here.
@admin.register(CellTower)
class CellTowerAdmin(admin.ModelAdmin):
    list_display = ('id', 'mcc', 'mnc', 'cell_id', 'lac', 'radio_type', 'lat', 'lon', 'source', 'updated_at')
    search_fields = ('mcc', 'mnc', 'cell_id', 'lac', 'radio_type', 'source')
    list_filter = ('source', 'radio_type', 'updated_at')