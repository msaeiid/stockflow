from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db import transaction

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class Category(TimeStampedModel):
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Supplier(TimeStampedModel):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Warehouse(TimeStampedModel):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True)
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Product(TimeStampedModel):
    name = models.CharField(max_length=200)
    sku = models.CharField("SKU",max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products'
        )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, related_name='products',null=True, blank=True
        )
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_threshold = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    
class Stock(TimeStampedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='stock_levels'
        )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name='stock_levels'
        )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'warehouse')
        ordering = ['product__name']

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}: {self.quantity}"
    
    @property
    def is_low(self):
        return self.quantity <= self.product.reorder_threshold
    

class StockMovement(TimeStampedModel):
    class MovementType(models.TextChoices):
        IN = 'IN', 'Stock In'
        OUT = 'OUT', 'Stock Out'
        
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='movements'
        )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name='movements'
    )
    movement_type = models.CharField(
        max_length=3, choices=MovementType.choices
    )
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at'] 
    
    def __str__(self):
        return f"{self.movement_type} {self.quantity} × {self.product.name} at {self.warehouse.name}"
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.movement_type == self.MovementType.OUT:
            stock = Stock.objects.filter(
                product=self.product, warehouse=self.warehouse
                ).first()
            available = stock.quantity if stock else 0
            if self.quantity > available:
                raise ValidationError(
                    f"Not enough stock. Available: {available}, requested: {self.quantity}."
                )
                
    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        with transaction.atomic():
            stock, _ = Stock.objects.select_for_update().get_or_create(
                product = self.product, warehouse=self.warehouse
            )
            if self.movement_type == self.MovementType.IN:
                stock.quantity += self.quantity
            else:
                stock.quantity -= self.quantity
            stock.save()
            super().save(*args, **kwargs)