from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.orders.models import Order, Payment
from app.orders.serializers import PaymentSerializer, PaymentCreateSerializer

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
        
        status_filter = self.request.query_params.get('payment_status', None)
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)
            
        method_filter = self.request.query_params.get('payment_method', None)
        if method_filter:
            queryset = queryset.filter(payment_method=method_filter)
            
        return queryset.order_by('-created_at')
    
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

                LoggerService.objects.create(
                    user=request.user,
                    action='UPDATE',
                    table_name='Payment',
                    description=f'Payment {payment.id} confirmed for order {order.id}'
                )
                
                return Response({
                    "message": "Payment confirmed successfully",
                    "payment_status": payment.payment_status,
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