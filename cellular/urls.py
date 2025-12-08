from django.urls import path
from .views import CellTowerCreateView, CellTowerSearchView, LocateUserView, CalibrationView, RefLossView

urlpatterns = [
    path('locate/', LocateUserView.as_view(), name='locate_user'),
    path('towers/add/', CellTowerCreateView.as_view(), name='add_tower'),
    path('towers/search/', CellTowerSearchView.as_view(), name='search_tower'),
    path('calibrate/', CalibrationView.as_view(), name='calibrate'),
    path('ref_loss/', RefLossView.as_view(), name='ref_loss'),
]