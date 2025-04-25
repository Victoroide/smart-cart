from django.db.models.signals import post_save
from django.dispatch import receiver
from app.orders.models import Payment
from app.authentication.models import CustomerLoyalty
from django.utils import timezone

@receiver(post_save, sender=Payment)
def update_customer_loyalty(sender, instance, **kwargs):
    if instance.payment_status == 'completed':
        order = instance.order
        user = order.user
        
        loyalty, created = CustomerLoyalty.objects.get_or_create(user=user)
        loyalty.total_orders += 1
        loyalty.total_spent += order.total_amount
        loyalty.last_order_date = timezone.now()
        
        points_earned = int(order.total_amount)
        loyalty.points += points_earned
        
        loyalty.update_tier()
        loyalty.save()

        from core.models import LoggerService
        LoggerService.objects.create(
            user=user,
            action='UPDATE',
            table_name='CustomerLoyalty',
            description=f'Updated loyalty status after order completion. New tier: {loyalty.tier}'
        )