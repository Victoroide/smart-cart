from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

class DiscountService:
    @staticmethod
    def get_loyalty_discount(user):

        if not user or not user.is_authenticated:
            return 0
            
        from app.orders.models import Order, Payment
        
        one_year_ago = timezone.now() - timedelta(days=365)
        completed_orders = Order.objects.filter(
            user=user,
            payment__payment_status='completed',
            payment__created_at__gte=one_year_ago
        )
        
        order_count = completed_orders.count()
        total_spent = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        if order_count >= 10 or total_spent >= 1000:
            return 15  # Platinum - 15% discount
        elif order_count >= 5 or total_spent >= 500:
            return 10  # Gold - 10% discount
        elif order_count >= 3 or total_spent >= 200:
            return 5   # Silver - 5% discount
        else:
            return 0   # Standard - no discount