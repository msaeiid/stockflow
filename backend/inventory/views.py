from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category, Product, Stock, StockMovement, Supplier, Warehouse
from .permissions import IsManagerOrReadOnly
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    StockMovementSerializer,
    StockSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManagerOrReadOnly]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsManagerOrReadOnly]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsManagerOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "supplier").all()
    serializer_class = ProductSerializer
    permission_classes = [IsManagerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "sku"]
    ordering_fields = ["name", "sale_price", "created_at"]


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.select_related("product", "warehouse").all()
    serializer_class = StockSerializer


@extend_schema_view(
    create=extend_schema(
        summary="Record a stock movement",
        description="Creates an IN or OUT movement. OUT movements are rejected "
        "if they exceed available stock.",
    ),
    list=extend_schema(summary="List all stock movements"),
)
class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "warehouse").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
