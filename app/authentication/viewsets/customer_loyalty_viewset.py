from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.authentication.models import CustomerLoyalty
from app.authentication.serializers.customer_loyalty_serializer import CustomerLoyaltySerializer
from services.discount_service import DiscountService
from app.authentication.viewsets.user_viewset import IsAdminOrOwner
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['CustomerLoyalty'])
class CustomerLoyaltyViewSet(viewsets.ModelViewSet):
    queryset = CustomerLoyalty.objects.all()
    serializer_class = CustomerLoyaltySerializer
    pagination_class = CustomPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk == 'me' and self.request.user.is_authenticated:
            return self.request.user.loyalty
        return super().get_object()
    
    @action(detail=False, methods=['get'], url_path='me')
    def my_loyalty(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            loyalty, created = CustomerLoyalty.objects.get_or_create(user=request.user)
            serializer = self.get_serializer(loyalty)
            return Response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='CustomerLoyalty',
                description=f'Error retrieving loyalty data: {str(e)}'
            )
            return Response({"error": "An error occurred while retrieving loyalty data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='adjust-tier')
    def adjust_tier(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            loyalty = self.get_object()
            loyalty.update_tier()
            loyalty.save()
            
            LoggerService.objects.create(
                user=request.user,
                action='UPDATE',
                table_name='CustomerLoyalty',
                description=f'Admin adjusted tier for user {loyalty.user.id}'
            )
            
            serializer = self.get_serializer(loyalty)
            return Response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='CustomerLoyalty',
                description=f'Error adjusting tier: {str(e)}'
            )
            return Response({"error": "An error occurred while adjusting tier"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'], url_path='status')
    def my_loyalty_status(self, request):
        """
        Returns the user's current loyalty status and discount information
        """
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            from app.orders.models import Order, Payment
            from django.db.models import Sum, Count
            import math
            
            completed_orders = Order.objects.filter(
                user=request.user,
                payment__payment_status='completed'
            )
            
            orders_count = completed_orders.count()
            total_spent = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
            
            discount_percentage = DiscountService.get_loyalty_discount(request.user)
            
            next_tier = None
            progress_percentage = 0
            
            if discount_percentage < 5:
                next_tier = "Silver"
                orders_needed = 3 - orders_count
                spent_needed = 200 - float(total_spent)
                progress_percentage = min(100, max(
                    (orders_count / 3) * 100,
                    (float(total_spent) / 200) * 100
                ))
            elif discount_percentage < 10:
                next_tier = "Gold"
                orders_needed = 5 - orders_count
                spent_needed = 500 - float(total_spent)
                progress_percentage = min(100, max(
                    ((orders_count - 3) / 2) * 100,
                    ((float(total_spent) - 200) / 300) * 100
                ))
            elif discount_percentage < 15:
                next_tier = "Platinum"
                orders_needed = 10 - orders_count
                spent_needed = 1000 - float(total_spent)
                progress_percentage = min(100, max(
                    ((orders_count - 5) / 5) * 100,
                    ((float(total_spent) - 500) / 500) * 100
                ))
            else:
                next_tier = None
                progress_percentage = 100
            
            current_tier = "Standard"
            if discount_percentage >= 15:
                current_tier = "Platinum"
            elif discount_percentage >= 10:
                current_tier = "Gold"
            elif discount_percentage >= 5:
                current_tier = "Silver"
                
            response_data = {
                "current_tier": current_tier,
                "discount_percentage": discount_percentage,
                "total_orders": orders_count,
                "total_spent": float(total_spent),
                "next_tier": next_tier,
                "progress_percentage": math.floor(progress_percentage)
            }
            
            if next_tier:
                response_data.update({
                    "orders_needed_for_next_tier": max(0, orders_needed),
                    "spent_needed_for_next_tier": max(0, spent_needed)
                })
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            from core.models import LoggerService
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Order',
                description=f'Error getting loyalty status: {str(e)}'
            )
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)