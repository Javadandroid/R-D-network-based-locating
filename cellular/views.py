"""
Legacy import path for DRF views.

The project now uses versioned API modules under `cellular.api.v1.*`.
This file is kept to avoid breaking older imports.
"""

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

__all__ = [
    "CalibrationView",
    "RefLossView",
    "LocateUserView",
    "SnapshotLocateView",
    "DbInfoView",
    "CellTowerBoundingBoxView",
    "CellTowerBulkUploadView",
    "CellTowerCreateView",
    "CellTowerSearchView",
    "ImportStartView",
    "ImportStatusView",
]

