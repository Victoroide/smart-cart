from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from app.orders.models import Payment, Order
from core.models import LoggerService
import json

@csrf_exempt
@require_POST
def paypal_webhook(request):
    payload = request.body
    
    try:
        payload_data = json.loads(payload)
        
        event_type = payload_data.get('event_type')
        
        if event_type == 'CHECKOUT.ORDER.APPROVED' or event_type == 'PAYMENT.CAPTURE.COMPLETED':
            resource = payload_data.get('resource', {})
            order_id = resource.get('id')
            
            if order_id:
                payment = Payment.objects.filter(transaction_id=order_id).first()
                
                if payment:
                    payment.payment_status = 'completed'
                    payment.save()
                    
                    order = payment.order
                    order.status = 'paid'
                    order.save()
                    
                    LoggerService.objects.create(
                        action='WEBHOOK',
                        table_name='Payment',
                        description=f'Payment for order {order.id} completed via PayPal webhook'
                    )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        LoggerService.objects.create(
            action='ERROR',
            table_name='Payment',
            description=f'Error in PayPal webhook: {str(e)}'
        )
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)