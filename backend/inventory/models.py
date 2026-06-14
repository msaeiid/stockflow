from django.db import models

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
    name = models.CharField(max_length=100,unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Warehouse(TimeStampedModel):
    name = models.CharField(max_length=100,unique=True)
    location = models.TextField(max_length=255, blank=True)
    
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