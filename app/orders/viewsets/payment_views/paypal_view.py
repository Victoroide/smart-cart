from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from django.conf import settings
from app.orders.models import Order, Payment
from core.models import LoggerService
import requests
from django.db import transaction
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Payment'])
class PayPalCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        with transaction.atomic():
            try:
                order_id = request.data.get('order_id')
                order = Order.objects.get(id=order_id, user=request.user)
                
                access_token = self.get_paypal_access_token()
                if not access_token:
                    return Response({'error': 'Could not authenticate with PayPal'}, status=status.HTTP_400_BAD_REQUEST)
                
                url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
                
                payload = {
                    "intent": "CAPTURE",
                    "purchase_units": [{
                        "amount": {
                            "currency_code": order.currency.upper(),
                            "value": str(order.total_amount)
                        },
                        "reference_id": str(order.id)
                    }],
                    "application_context": {
                        "return_url": f"{settings.FRONTEND_URL}/customer/carrito?payment=success",
                        "cancel_url": f"{settings.FRONTEND_URL}/customer/carrito?payment=cancel",
                        "brand_name": "Smart Cart",
                        "user_action": "PAY_NOW"
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload)
                data = response.json()
                
                if response.status_code == 201:
                    if hasattr(order, 'payment'):
                        payment = order.payment
                    else:
                        payment = Payment.objects.create(
                            order=order,
                            amount=order.total_amount,
                            payment_method='paypal',
                            payment_status='pending'
                        )
                    
                    payment.transaction_id = data['id']
                    payment.payment_status = 'processing'
                    payment_details = {
                        'paypal_order_id': data['id'],
                        'status': data['status'],
                        'links': {link['rel']: link['href'] for link in data['links']}
                    }
                    payment.payment_details = payment_details
                    payment.save()
                    
                    approve_link = next((link for link in data['links'] if link['rel'] == 'approve'), None)
                    
                    LoggerService.objects.create(
                        user=request.user,
                        action='PAYMENT_STARTED',
                        table_name='Order',
                        description=f'Payment initiated for order {order.id} with PayPal'
                    )
                    
                    return Response({
                        'approve_url': approve_link['href'] if approve_link else None,
                        'order_id': data['id']
                    })
                else:
                    return Response({
                        'error': data.get('message', 'Unknown error with PayPal'),
                        'details': data
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Payment',
                    description=f'Error creating PayPal order: {str(e)}'
                )
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