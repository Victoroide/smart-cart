from django.db import models
from core.models import TimestampedModel

class ProductCategory(TimestampedModel):
    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)