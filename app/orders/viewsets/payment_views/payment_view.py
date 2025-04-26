from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from base import settings
from app.orders.models import Order, Payment
import stripe
import requests
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Payment'])
class PaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            
            if order.user != request.user and not request.user.is_staff:
                return Response({'error': 'You do not have permission to view this order'}, 
                               status=status.HTTP_403_FORBIDDEN)
            
            if not hasattr(order, 'payment'):
                return Response({'status': 'no_payment', 'message': 'No payment has been initiated for this order'})
            
            payment = order.payment
            
            if payment.payment_status == 'completed':
                return Response({
                    'status': 'completed',
                    'payment_method': payment.payment_method,
                    'amount': float(payment.amount),
                    'transaction_id': payment.transaction_id,
                    'date': payment.updated_at
                })
            
            if payment.payment_method == 'stripe' and payment.transaction_id:
                stripe.api_key = settings.STRIPE_API_KEY
                session = stripe.checkout.Session.retrieve(payment.transaction_id)
                
                if session.payment_status == 'paid':
                    payment.payment_status = 'completed'
                    payment.save()
                    
                    return Response({
                        'status': 'completed',
                        'payment_method': 'stripe',
                        'amount': float(payment.amount),
                        'transaction_id': payment.transaction_id,
                        'date': payment.updated_at
                    })
                else:
                    return Response({
                        'status': 'pending',
                        'payment_method': 'stripe',
                        'session_status': session.status,
                        'payment_status': session.payment_status
                    })
            
            elif payment.payment_method == 'paypal' and payment.transaction_id:
                access_token = self.get_paypal_access_token()
                
                if access_token:
                    url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{payment.transaction_id}"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    }
                    
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get('status') == 'COMPLETED':
                            payment.payment_status = 'completed'
                            payment.save()
                            
                            return Response({
                                'status': 'completed',
                                'payment_method': 'paypal',
                                'amount': float(payment.amount),
                                'transaction_id': payment.transaction_id,
                                'date': payment.updated_at
                            })
                        else:
                            return Response({
                                'status': 'pending',
                                'payment_method': 'paypal',
                                'paypal_status': data.get('status')
                            })
            
            return Response({
                'status': payment.payment_status,
                'payment_method': payment.payment_method
            })
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_paypal_access_token(self):
        try:
            url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
            auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
            headers = {"Accept": "application/json", "Accept-Language": "en_US"}
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(url, auth=auth, headers=headers, data=data)
            if response.status_code == 200:
                return response.json()["access_token"]
            return None
        except Exception:
            return None