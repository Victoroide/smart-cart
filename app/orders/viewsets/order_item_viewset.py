from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.orders.models import Order, OrderItem
from app.orders.serializers import OrderItemSerializer, OrderItemCreateSerializer
from app.products.models import Product, Inventory
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['OrderItem'])
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by('-created_at')
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderItemCreateSerializer
        return OrderItemSerializer
    
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                order_id = request.data.get('order_id')
                if not order_id:
                    return Response(
                        {"error": "order_id is required"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    order = Order.objects.get(id=order_id)
                    if order.user != request.user and not request.user.is_staff:
                        return Response(
                            {"error": "You don't have permission to add items to this order"}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Order.DoesNotExist:
                    return Response(
                        {"error": "Order not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                product_id = request.data.get('product_id')
                quantity = request.data.get('quantity', 1)
                
                try:
                    product = Product.objects.get(id=product_id, active=True)
                    
                    unit_price = product.price_usd if order.currency == 'USD' else product.price_bs
                    
                    inventory = Inventory.objects.get(product=product)
                    if inventory.stock < quantity:
                        return Response(
                            {"error": f"Insufficient inventory for {product.name}. Available: {inventory.stock}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    order_item = OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price
                    )
                    
                    order.total_amount += unit_price * quantity
                    order.save()
                    
                    LoggerService.objects.create(
                        user=request.user,
                        action='CREATE',
                        table_name='OrderItem',
                        description=f'Added item to cart: {product.name} (x{quantity})'
                    )
                    
                    serializer = OrderItemSerializer(order_item)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                    
                except Product.DoesNotExist:
                    return Response(
                        {"error": "Product not found or not active"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
                except Exception as e:
                    return Response(
                        {"error": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='OrderItem',
                    description='Error adding item to cart: ' + str(e)
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                order = instance.order
                
                if hasattr(order, 'payment') and order.payment.payment_status == 'completed':
                    return Response(
                        {"error": "Cannot modify items in an order that has been paid"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                original_quantity = instance.quantity
                
                response = super().partial_update(request, *args, **kwargs)
                
                updated_instance = self.get_object()
                if 'quantity' in request.data and updated_instance.quantity != original_quantity:
                    quantity_difference = updated_instance.quantity - original_quantity
                    amount_change = updated_instance.unit_price * quantity_difference
                    order.total_amount += amount_change
                    order.save()
                
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='OrderItem',
                    description='Partially updated order item ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='OrderItem',
                    description='Error on partial_update order item: ' + str(e)
                )
                raise e
    
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                order = instance.order
                
                if hasattr(order, 'payment') and order.payment.payment_status == 'completed':
                    return Response(
                        {"error": "Cannot remove items from an order that has been paid"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                amount_to_subtract = instance.unit_price * instance.quantity
                
                instance.delete()
                
                remaining_items = OrderItem.objects.filter(order=order).count()
                
                if remaining_items == 0:
                    order.total_amount = 0
                    order.save()
                    LoggerService.objects.create(
                        user=request.user,
                        action='UPDATE',
                        table_name='Order',
                        description=f'Reset empty cart (order {order.id})'
                    )
                else:
                    order.total_amount -= amount_to_subtract
                    order.save()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='DELETE',
                    table_name='OrderItem',
                    description='Removed item from cart'
                )
                
                return Response(status=status.HTTP_204_NO_CONTENT)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='OrderItem',
                    description='Error removing item from cart: ' + str(e)
                )
                raise e