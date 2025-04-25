from django.db import models
from django.conf import settings
from core.models import TimestampedModel

class CustomerLoyalty(TimestampedModel):
    LOYALTY_TIERS = (
        ('standard', 'Standard'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loyalty', primary_key=True)
    tier = models.CharField(max_length=20, choices=LOYALTY_TIERS, default='standard')
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    points = models.IntegerField(default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    
    def get_discount_percentage(self):
        discounts = {
            'standard': 0,
            'silver': 5,
            'gold': 10,
            'platinum': 15
        }
        return discounts.get(self.tier, 0)
    
    def update_tier(self):
        if self.total_spent >= 1000 or self.total_orders >= 10:
            self.tier = 'platinum'
        elif self.total_spent >= 500 or self.total_orders >= 5:
            self.tier = 'gold'
        elif self.total_spent >= 200 or self.total_orders >= 3:
            self.tier = 'silver'
        else:
            self.tier = 'standard'