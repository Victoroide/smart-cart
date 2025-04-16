from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from app.orders.models import Payment, Order
from core.models import LoggerService
import stripe
import json

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        stripe.api_key = settings.STRIPE_API_KEY
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        event_data = event['data']['object']
        
        if event['type'] == 'checkout.session.completed':
            session_id = event_data['id']
            
            payment = Payment.objects.select_related('order').filter(transaction_id=session_id).first()
            
            if payment and payment.payment_status != 'completed':
                payment.payment_status = 'completed'
                payment.save()
                
                LoggerService.objects.create(
                    action='WEBHOOK',
                    table_name='Payment',
                    description=f'Payment for order {payment.order.id} completed via Stripe webhook'
                )
        
        return HttpResponse(status=200)
        
    except Exception as e:
        LoggerService.objects.create(
            action='ERROR',
            table_name='Payment',
            description=f'Error in Stripe webhook: {str(e)}'
        )
        return HttpResponse(status=400)