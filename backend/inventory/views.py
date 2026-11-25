from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connection
from django.db.models import DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import filters, serializers, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
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
    DashboardStatsSerializer,
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
    filterset_fields = ["warehouse", "product"]


@extend_schema_view(
    create=extend_schema(
        summary="Record a stock movement",
        description="Creates an IN or OUT movement. OUT movements are rejected "
        "if they exceed available stock.",
    ),
    list=extend_schema(summary="List all stock movements"),
)
class StockMovementViewSet(viewsets.ModelViewSet):
    """Movements are a ledger: they can be listed and recorded, never edited or
    deleted (that would leave the stock levels out of step)."""

    queryset = StockMovement.objects.select_related("product", "warehouse").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["product", "warehouse", "movement_type"]


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    cache_key = "dashboard_stats"
    cache_timeout = 30

    @extend_schema(responses=DashboardStatsSerializer)
    def get(self, request):
        cached = cache.get(self.cache_key)
        if cached is not None:
            return Response(cached)

        low_stock_count = Stock.objects.filter(
            quantity__lte=F("product__reorder_threshold")
        ).count()

        inventory_value = Stock.objects.aggregate(
            value=Coalesce(
                Sum(F("quantity") * F("product__cost_price"), output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            )
        )["value"]

        top_stock = Stock.objects.select_related("product").order_by("-quantity")[:5]

        data = DashboardStatsSerializer(
            {
                "total_products": Product.objects.filter(is_active=True).count(),
                "low_stock_count": low_stock_count,
                "inventory_value": inventory_value,
                "top_products": [
                    {"name": s.product.name, "quantity": s.quantity} for s in top_stock
                ],
            }
        ).data
        cache.set(self.cache_key, data, timeout=self.cache_timeout)
        return Response(data)


class HealthView(APIView):
    """Liveness/readiness probe for the container healthcheck."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(
        responses={
            200: inline_serializer("Health", {"status": serializers.CharField()}),
            503: OpenApiResponse(description="Database unavailable"),
        }
    )
    def get(self, request):
        try:
            connection.ensure_connection()
        except Exception:
            return Response({"status": "database unavailable"}, status=503)
        return Response({"status": "ok"})


class DemoInfoView(APIView):
    """Tells the login page whether this is a public demo and, when the operator
    allows it (DEMO_SHOW_CREDENTIALS), which shared login to use."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses=inline_serializer(
            "DemoInfo",
            {
                "demo_mode": serializers.BooleanField(),
                "username": serializers.CharField(allow_null=True),
                "password": serializers.CharField(allow_null=True),
            },
        )
    )
    def get(self, request):
        show = settings.DEMO_MODE and settings.DEMO_SHOW_CREDENTIALS and settings.DEMO_PASSWORD
        return Response(
            {
                "demo_mode": settings.DEMO_MODE,
                "username": settings.DEMO_USERNAME if show else None,
                "password": settings.DEMO_PASSWORD if show else None,
            }
        )


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("items__product").all()
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    @extend_schema(request=OrderCreateSerializer, responses={201: OrderReadSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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

        order = self.get_queryset().get(pk=order.pk)
        read = OrderReadSerializer(order, context=self.get_serializer_context())
        return Response(read.data, status=status.HTTP_201_CREATED)
