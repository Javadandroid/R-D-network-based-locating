from django.contrib import admin, messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from .choices import DatasetSource
from .forms import CellTowerImportForm
from .models import CellTower
from .utils.importers import import_towers_from_csv
from .models import TowerLookupLog


# Register your models here.
@admin.register(CellTower)
class CellTowerAdmin(admin.ModelAdmin):
    list_display = ('id', 'mcc', 'mnc', 'cell_id', 'lac', 'radio_type','range_m','earfcn','samples', 'lat', 'lon', 'source','tx_power', 'checked_count', 'verified_count', 'created_at')
    search_fields = ('mcc', 'mnc', 'cell_id', 'lac', 'radio_type', 'source')
    list_filter = ('source', 'radio_type', 'updated_at')
    change_list_template = "admin/celltower/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='celltower_import'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CellTowerImportForm(request.POST, request.FILES)
            if form.is_valid():
                dataset_source = form.cleaned_data['dataset_source']
                stats = import_towers_from_csv(
                    form.cleaned_data['csv_file'],
                    dataset_source=dataset_source,
                    update_existing=form.cleaned_data.get('update_existing', True),
                )
                self.message_user(
                    request,
                    f"{stats['created']}  created and {stats['updated']} updated.",
                    level=messages.SUCCESS
                )
                if stats["errors"]:
                    self.message_user(request, " / ".join(stats["errors"]), level=messages.WARNING)
                return redirect("..")
        else:
            form = CellTowerImportForm()

        context = {**self.admin_site.each_context(request), "form": form}
        return TemplateResponse(request, "admin/celltower/import_form.html", context)


@admin.register(TowerLookupLog)
class TowerLookupLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "provider",
        "success",
        "mcc",
        "mnc",
        "lac",
        "cell_id",
        "pci",
        "earfcn",
        "accuracy_m",
    )
    list_filter = ("provider", "success", "created_at")
    search_fields = ("provider", "request_url", "error")
    readonly_fields = (
        "created_at",
        "provider",
        "mcc",
        "mnc",
        "lac",
        "cell_id",
        "pci",
        "earfcn",
        "success",
        "lat",
        "lon",
        "accuracy_m",
        "request_url",
        "request_body",
        "response_body",
        "error",
    )
