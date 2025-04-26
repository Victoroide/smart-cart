from django.db import models
from core.models import TimestampedModel
from app.orders.models.order_model import Order
from app.products.models.product_model import Product

class Feedback(TimestampedModel):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='feedbacks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='feedbacks', null=True, blank=True)
    delivery_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    product_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    delivery_comment = models.TextField(null=True, blank=True)
    product_comment = models.TextField(null=True, blank=True)
    user = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, related_name='feedbacks')
    
    class Meta:
        unique_together = ('order', 'product')