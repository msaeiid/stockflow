from rest_framework import serializers

from .models import Category, Order, OrderItem, Product, Stock, StockMovement, Supplier, Warehouse


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "phone", "address", "created_at"]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(read_only=True, source="category.name")
    supplier_name = serializers.CharField(read_only=True, default=None, source="supplier.name")

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "category",
            "category_name",
            "supplier",
            "supplier_name",
            "cost_price",
            "sale_price",
            "reorder_threshold",
            "is_active",
            "created_at",
        ]


class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(read_only=True, source="product.name")
    warehouse_name = serializers.CharField(read_only=True, source="warehouse.name")
    is_low = serializers.BooleanField(read_only=True)

    class Meta:
        model = Stock
        fields = [
            "id",
            "product",
            "product_name",
            "warehouse",
            "warehouse_name",
            "quantity",
            "is_low",
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id", "product", "warehouse", "movement_type", "quantity", "note", "created_at"]

    def validate(self, attrs):
        from django.core.exceptions import ValidationError as DjangoValidationError

        instance = StockMovement(**attrs)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from None
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_name", "quantity", "unit_price", "subtotal"]
        read_only_fields = ["unit_price"]


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "reference",
            "warehouse",
            "customer_name",
            "status",
            "note",
            "total",
            "items",
            "created_at",
        ]


class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    customer_name = serializers.CharField(max_length=150)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)
    items = OrderItemWriteSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("An order must contain at least one item.")
        return value
