from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Category,
    Order,
    Product,
    Stock,
    StockMovement,
    Supplier,
    Warehouse,
)
from .permissions import IsManagerOrReadOnly
from .serializers import (
    CategorySerializer,
    OrderCreateSerializer,
    OrderReadSerializer,
    ProductSerializer,
    StockMovementSerializer,
    StockSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)
from .services import create_order


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active", "supplier"]
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


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cached = cache.get("dashboard_stats")

        if cached is not None:
            return Response(cached)

        total_products = Product.objects.filter(is_active=True).count()

        low_stock = [
            s
            for s in Stock.objects.select_related("product")
            if s.quantity <= s.product.reorder_threshold
        ]

        inventory_value = Stock.objects.aggregate(
            value=Coalesce(
                Sum(F("quantity") * F("product__cost_price"), output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            )
        )["value"]

        top_stock = Stock.objects.select_related("product").order_by("-quantity")[:5]

        data = {
            "total_products": total_products,
            "low_stock_count": len(low_stock),
            "inventory_value": inventory_value,
            "top_products": [{"name": s.product.name, "quantity": s.quantity} for s in top_stock],
        }
        cache.set("dashboard_stats", data, timeout=30)
        return Response()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("items__product").all()
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        items = [
            {"product": entry["product"], "quantity": entry["quantity"]} for entry in data["items"]
        ]

        try:
            order = create_order(
                warehouse=data["warehouse"],
                customer_name=data["customer_name"],
                items=items,
                note=data.get("note", ""),
            )

        except DjangoValidationError as exc:
            raise DRFValidationError({"detail": exc.messages}) from exc

        read = OrderReadSerializer(order)
        return Response(read.data, status=status.HTTP_201_CREATED)
