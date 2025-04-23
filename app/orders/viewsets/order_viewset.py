from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.orders.models import Order, OrderItem
from app.orders.serializers import OrderSerializer, OrderCreateSerializer
from base import settings

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(active=True).order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        queryset = Order.objects.filter(active=True)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            try:
                order = serializer.save(user=request.user)
                
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Order',
                    description='Created order ' + str(order.id)
                )
                
                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Order',
                    description='Error on create order: ' + str(e)
                )
                raise e
    
    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Order',
                    description='Partially updated order ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Order',
                    description='Error on partial_update order: ' + str(e)
                )
                raise e
    
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                
                if hasattr(instance, 'payment') and instance.payment.payment_status == 'completed':
                    return Response(
                        {"error": "Cannot delete an order that has been paid"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                instance.active = False
                instance.save()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Order',
                    description='Soft-deleted order ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Order',
                    description='Error on delete order: ' + str(e)
                )
                raise e
    
    @action(detail=True, methods=['get'], url_path='costs')
    def get_costs(self, request, pk=None):
        try:
            order = self.get_object()
            
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to view this order's costs"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            items = OrderItem.objects.filter(order=order)
            
            if not items.exists():
                return Response(
                    {"error": "This order has no items"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            subtotal = sum(item.unit_price * item.quantity for item in items)
            
            tax_rate = getattr(settings, 'TAX_RATE', 0.16)
            tax_amount = subtotal * tax_rate
            
            shipping_cost = getattr(settings, 'SHIPPING_COST', 10.0)
            discount = 0
            
            total = subtotal - discount
            
            if order.total_amount != total:
                order.total_amount = total
                order.save()
            
            payment_status = 'not_started'
            payment_method = None
            
            if hasattr(order, 'payment'):
                payment_status = order.payment.payment_status
                payment_method = order.payment.payment_method
            
            cost_breakdown = {
                "order_id": order.id,
                "subtotal": float(subtotal),
                "tax_rate": float(tax_rate * 100),
                # "tax_amount": float(tax_amount),
                # "shipping_cost": float(shipping_cost),
                "discount": float(discount),
                "total": float(total),
                "currency": order.currency,
                "payment_status": payment_status,
                "payment_method": payment_method,
                "items": [
                    {
                        "product_id": item.product.id,
                        "product_name": item.product.name,
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "total_price": float(item.unit_price * item.quantity)
                    } for item in items
                ],
                "created_at": order.created_at,
                "updated_at": order.updated_at
            }
            
            return Response(cost_breakdown, status=status.HTTP_200_OK)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Order',
                description=f'Error getting order costs: {str(e)}'
            )
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )