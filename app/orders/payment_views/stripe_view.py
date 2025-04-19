from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from django.conf import settings
from app.orders.models import Order, Payment
from core.models import LoggerService
import stripe
from django.db import transaction

class StripeCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        with transaction.atomic():
            try:
                order_id = request.data.get('order_id')
                order = Order.objects.get(id=order_id, user=request.user)
                
                stripe.api_key = settings.STRIPE_API_KEY
                
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': order.currency.lower(),
                            'product_data': {
                                'name': f'Order #{order.id}',
                                'description': f'Purchase from Smart Cart',
                            },
                            'unit_amount': int(order.total_amount * 100),
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    metadata={
                        'order_id': order.id
                    }
                )
                
                if hasattr(order, 'payment'):
                    payment = order.payment
                else:
                    payment = Payment.objects.create(
                        order=order,
                        amount=order.total_amount,
                        payment_method='stripe',
                        payment_status='pending'
                    )
                
                payment.transaction_id = checkout_session.id
                payment.payment_status = 'processing'
                payment.save()
                
                order.status = 'payment_pending'
                order.save()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='PAYMENT_STARTED',
                    table_name='Order',
                    description=f'Payment initiated for order {order.id} with Stripe Checkout'
                )
                
                return Response({
                    'checkout_url': checkout_session.url,
                    'session_id': checkout_session.id
                })
                
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Payment',
                    description=f'Error creating Stripe checkout session: {str(e)}'
                )
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)