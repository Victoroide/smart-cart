from django.db import models
from core.models import TimestampedModel
from app.products.models.brand_model import Brand

class Warranty(TimestampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    duration_months = models.PositiveIntegerField(default=12)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='warranties')
    active = models.BooleanField(default=True)