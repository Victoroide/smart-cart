from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from .models import Order, OrderItem, Payment, Delivery
from .serializers import *
from base import settings

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(active=True)
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                order = serializer.save()
                
                response_serializer = OrderSerializer(order, context=self.get_serializer_context())
                response_data = response_serializer.data
                
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Order',
                    description='Created order ' + str(order.id)
                )
                
                return Response(response_data, status=status.HTTP_201_CREATED)
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
                "status": order.status,
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

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='OrderItem',
                    description='Created order item ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='OrderItem',
                    description='Error on create order item: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
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
                instance.delete()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='OrderItem',
                    description='Deleted order item ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='OrderItem',
                    description='Error on delete order item: ' + str(e)
                )
                raise e

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    pagination_class = CustomPagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        queryset = Payment.objects.all()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(order__user=self.request.user)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                order_id = serializer.validated_data['order'].id
                payment_method = serializer.validated_data['payment_method']
                
                order = Order.objects.select_for_update().get(id=order_id)
                
                if order.user != request.user and not request.user.is_staff:
                    return Response(
                        {"error": "You don't have permission to process payment for this order"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                if hasattr(order, 'payment'):
                    if order.payment.payment_status == 'completed':
                        return Response(
                            {"error": "This order has already been paid"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    existing_payment = order.payment
                    existing_payment.payment_method = payment_method
                    existing_payment.save()
                    payment = existing_payment
                else:
                    payment = Payment.objects.create(
                        order=order,
                        amount=order.total_amount,
                        payment_method=payment_method
                    )
                
                payment_response = {}
                
                if payment_method == 'stripe':
                    stripe_service = StripePaymentService()
                    payment_response = stripe_service.create_payment_intent(
                        amount=float(payment.amount),
                        metadata={"order_id": order.id}
                    )
                    
                    if payment_response["success"]:
                        payment.payment_intent_id = payment_response["payment_intent_id"]
                        payment.payment_status = 'processing'
                        payment.save()
                    else:
                        return Response(
                            {"error": payment_response["error"]},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                elif payment_method == 'paypal':
                    paypal_service = PayPalPaymentService()
                    payment_response = paypal_service.create_order(
                        amount=float(payment.amount),
                        reference_id=str(order.id)
                    )
                    
                    if payment_response["success"]:
                        payment.transaction_id = payment_response["order_id"]
                        payment.payment_status = 'processing'
                        payment.payment_details = payment_response
                        payment.save()
                    else:
                        return Response(
                            {"error": payment_response["error"]},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                order.status = 'payment_pending'
                order.save()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Payment',
                    description=f'Payment initiated for order {order.id}'
                )
                
                result = self.get_serializer(payment)
                response_data = {
                    **result.data,
                    "payment_details": payment.payment_details,
                }
                
                if payment_method == 'stripe' and payment_response.get("client_secret"):
                    response_data["client_secret"] = payment_response["client_secret"]
                    
                return Response(response_data, status=status.HTTP_200_OK)
            
            except Order.DoesNotExist:
                return Response(
                    {"error": "Order not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Payment',
                    description=f'Error creating payment: {str(e)}'
                )
                return Response(
                    {"error": f"An error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_payment(self, request, pk=None):
        try:
            payment = self.get_object()
            
            if payment.order.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to confirm this payment"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            if payment.payment_status == 'completed':
                return Response({"message": "Payment already completed"})
                
            result = {}
            
            if payment.payment_method == 'stripe':
                stripe_service = StripePaymentService()
                result = stripe_service.confirm_payment(payment.payment_intent_id)
            elif payment.payment_method == 'paypal':
                paypal_service = PayPalPaymentService()
                result = paypal_service.capture_order(payment.transaction_id)
            else:
                return Response(
                    {"error": f"Confirmation not supported for {payment.payment_method}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if result.get("success") and result.get("is_paid", False):
                payment.payment_status = 'completed'
                payment.save()
                
                order = payment.order
                order.status = 'paid'
                order.save()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='UPDATE',
                    table_name='Payment',
                    description=f'Payment {payment.id} confirmed for order {order.id}'
                )
                
                return Response({
                    "message": "Payment confirmed successfully",
                    "payment_status": payment.payment_status,
                    "order_status": order.status
                })
            else:
                error_message = result.get("error", "Payment could not be confirmed")
                return Response(
                    {"error": error_message},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Payment',
                description=f'Error confirming payment: {str(e)}'
            )
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Delivery',
                    description='Created delivery ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Delivery',
                    description='Error on create delivery: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Delivery',
                    description='Partially updated delivery ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Delivery',
                    description='Error on partial_update delivery: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.delete()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Delivery',
                    description='Deleted delivery ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Delivery',
                    description='Error on delete delivery: ' + str(e)
                )
                raise e
