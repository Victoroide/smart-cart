from django.db import models
from core.models import TimestampedModel

class Brand(TimestampedModel):
    name = models.CharField(max_length=60, unique=True)
    active = models.BooleanField(default=True)