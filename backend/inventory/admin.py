from django.contrib import admin

from .models import Category, Product, Stock, StockMovement, Supplier, Warehouse


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "sale_price", "reorder_threshold", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("category", "is_active")


admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Warehouse)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "movement_type", "quantity", "created_at")
    list_filter = ("movement_type", "warehouse")


admin.site.register(Stock)
