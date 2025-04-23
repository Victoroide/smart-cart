from django.db import models
from core.models import TimestampedModel
from app.orders.models.order_model import Order

class Delivery(TimestampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_address = models.CharField(max_length=255)
    delivery_status = models.CharField(max_length=20, default='pending')
    tracking_info = models.CharField(max_length=255, null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)