from django.db import models
from core.models import TimestampedModel
from base.storage import PublicMediaStorage

class Brand(TimestampedModel):
    name = models.CharField(max_length=60, unique=True)
    active = models.BooleanField(default=True)

class ProductCategory(TimestampedModel):
    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)

class Product(TimestampedModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    image_url = models.FileField(storage=PublicMediaStorage(custom_path='products/images'), null=True, blank=True)
    technical_specifications = models.TextField(null=True, blank=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_bs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class Inventory(TimestampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory', primary_key=True)
    stock = models.PositiveIntegerField(default=0)

class Warranty(TimestampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='warranty')
    warranty_type = models.CharField(max_length=50)
    details = models.TextField(null=True, blank=True)
