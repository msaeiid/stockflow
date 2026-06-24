from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    DashboardStatsView,
    ProductViewSet,
    StockMovementViewSet,
    StockViewSet,
    SupplierViewSet,
    WarehouseViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"suppliers", SupplierViewSet)
router.register(r"warehouses", WarehouseViewSet)
router.register(r"products", ProductViewSet)
router.register(r"stocks", StockViewSet)
router.register(r"movements", StockMovementViewSet)

urlpatterns = router.urls + [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
]
