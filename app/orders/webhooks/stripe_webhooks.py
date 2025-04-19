from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
import json
from django.conf import settings
from app.orders.models import Order, Payment
from core.models import LoggerService

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    if event.type == 'checkout.session.completed':
        session = event.data.object
        
        payment = Payment.objects.filter(transaction_id=session.id).first()
        if payment and payment.payment_status == 'completed':
            return HttpResponse(status=200)
            
        order_id = int(session.metadata.get('order_id'))
        
        try:
            order = Order.objects.get(id=order_id)
            
            if payment:
                payment.payment_status = 'completed'
                payment.save()
            else:
                Payment.objects.create(
                    order=order,
                    amount=order.total_amount,
                    payment_method='stripe',
                    payment_status='completed',
                    transaction_id=session.id
                )
            
            order.status = 'paid'
            order.save()
            
            LoggerService.objects.create(
                action='PAYMENT_COMPLETED',
                table_name='Order',
                description=f'Payment completed for order {order.id}'
            )
            
        except Order.DoesNotExist:
            LoggerService.objects.create(
                action='ERROR',
                table_name='Payment',
                description=f'Order not found for completed payment: {order_id}'
            )
            
    return HttpResponse(status=200)