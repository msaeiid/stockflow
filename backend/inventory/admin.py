from django.contrib import admin

from .models import Category, Order, OrderItem, Product, Stock, StockMovement, Supplier, Warehouse


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "sale_price", "reorder_threshold", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("category", "is_active")
    list_select_related = ("category",)


admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Warehouse)


class ReadOnlyAdminMixin:
    """Stock levels, movements and orders are written only through the ledger
    (StockMovement / create_order); editing them by hand would desynchronise
    the stock quantities."""

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockMovement)
class StockMovementAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    # Adding a movement is allowed: it updates the stock like the API does.
    list_display = ("product", "warehouse", "movement_type", "quantity", "created_at")
    list_filter = ("movement_type", "warehouse")
    list_select_related = ("product", "warehouse")


@admin.register(Stock)
class StockAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity")
    list_filter = ("warehouse",)
    list_select_related = ("product", "warehouse")

    def has_add_permission(self, request):
        return False


class OrderItemInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = OrderItem
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("reference", "customer_name", "warehouse", "status", "created_at")
    list_filter = ("status", "warehouse")
    list_select_related = ("warehouse",)
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False
