from django.db import models
from core.models import TimestampedModel
from app.authentication.models import User
from app.products.models import Product

class Order(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='pending')
    payment_method = models.CharField(max_length=20, null=True, blank=True)
    active = models.BooleanField(default=True)

class OrderItem(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(TimestampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='initiated')
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

class Delivery(TimestampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_address = models.CharField(max_length=255)
    delivery_status = models.CharField(max_length=20, default='pending')
    tracking_info = models.CharField(max_length=255, null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
