from django.db import models
from core.models import TimestampedModel
from app.authentication.models import User

class Order(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    active = models.BooleanField(default=True)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_percentage = models.IntegerField(default=0)