from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    DashboardStatsView,
    DemoInfoView,
    HealthView,
    OrderViewSet,
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
router.register("orders", OrderViewSet)

urlpatterns = router.urls + [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("health/", HealthView.as_view(), name="health"),
    path("demo/", DemoInfoView.as_view(), name="demo-info"),
]
