from django.urls import path

from cellular.api.v1.views.calibration import CalibrationView, RefLossView
from cellular.api.v1.views.positioning import LocateUserView, SnapshotLocateView
from cellular.api.v1.views.system import DbInfoView
from cellular.api.v1.views.towers import (
    CellTowerBoundingBoxView,
    CellTowerBulkUploadView,
    CellTowerCreateView,
    CellTowerSearchView,
    ImportStartView,
    ImportStatusView,
)

urlpatterns = [
    # --- Positioning ---
    path("locate/", LocateUserView.as_view(), name="locate_user"),
    path("snapshot/locate/", SnapshotLocateView.as_view(), name="snapshot_locate"),

    # --- Towers ---
    path("towers/add/", CellTowerCreateView.as_view(), name="add_tower"),
    path("towers/search/", CellTowerSearchView.as_view(), name="search_tower"),
    path("towers/within/", CellTowerBoundingBoxView.as_view(), name="towers_within_bbox"),
    path("towers/import/", CellTowerBulkUploadView.as_view(), name="import_towers"),
    path("towers/import-start/", ImportStartView.as_view(), name="import_start"),
    path("towers/import-status/<str:job_id>/", ImportStatusView.as_view(), name="import_status"),

    # --- Calibration ---
    path("calibrate/", CalibrationView.as_view(), name="calibrate"),
    path("ref_loss/", RefLossView.as_view(), name="ref_loss"),

    # --- System ---
    path("system/db-info/", DbInfoView.as_view(), name="db_info"),
]
