from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from app.orders.models import Payment
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
            custom_id = resource.get('custom_id')
            transaction_id = resource.get('id')
            
            if custom_id and transaction_id:
                payment = Payment.objects.select_related('order').filter(
                    order__id=custom_id, 
                    transaction_id=transaction_id
                ).first()
                
                if not payment:
                    payment = Payment.objects.select_related('order').filter(
                        order__id=custom_id
                    ).first()
                    
                    if payment:
                        payment.transaction_id = transaction_id
                        
                if payment and payment.payment_status != 'completed':
                    payment.payment_status = 'completed'
                    payment.save()
                    
                    LoggerService.objects.create(
                        action='WEBHOOK',
                        table_name='Payment',
                        description=f'Payment for order {payment.order.id} completed via PayPal webhook'
                    )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        LoggerService.objects.create(
            action='ERROR',
            table_name='Payment',
            description=f'Error in PayPal webhook: {str(e)}'
        )
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)