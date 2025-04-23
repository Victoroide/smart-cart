from django.db import models
from core.models import TimestampedModel
from app.products.models.product_model import Product

class Inventory(TimestampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory', primary_key=True)
    stock = models.PositiveIntegerField(default=0)