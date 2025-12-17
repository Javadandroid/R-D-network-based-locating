from django.urls import path
from .views import (
    CellTowerCreateView,
    CellTowerSearchView,
    LocateUserView,
    CalibrationView,
    RefLossView,
    CellTowerBulkUploadView,
    CellTowerBoundingBoxView,
    ImportStartView,
    ImportStatusView,
    SnapshotLocateView,
    DbInfoView,
)

urlpatterns = [
    path('locate/', LocateUserView.as_view(), name='locate_user'),
    path('towers/add/', CellTowerCreateView.as_view(), name='add_tower'),
    path('towers/search/', CellTowerSearchView.as_view(), name='search_tower'),
    path('towers/import/', CellTowerBulkUploadView.as_view(), name='import_towers'),
    path('towers/within/', CellTowerBoundingBoxView.as_view(), name='towers_within_bbox'),
    path('towers/import-start/', ImportStartView.as_view(), name='import_start'),
    path('towers/import-status/<str:job_id>/', ImportStatusView.as_view(), name='import_status'),
    path('snapshot/locate/', SnapshotLocateView.as_view(), name='snapshot_locate'),
    path('system/db-info/', DbInfoView.as_view(), name='db_info'),
    path('calibrate/', CalibrationView.as_view(), name='calibrate'),
    path('ref_loss/', RefLossView.as_view(), name='ref_loss'),
]
