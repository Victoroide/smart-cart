from django.utils import timezone
from app.orders.models import Delivery, Order
from app.orders.models.delivery_address_model import DeliveryAddress
from app.parameter.models import Country, State, City

def create_delivery_after_payment(order):
    if hasattr(order, 'delivery'):
        return
    
    try:
        user = order.user
        
        delivery_address_id = order.metadata.get('delivery_address_id') if hasattr(order, 'metadata') and order.metadata else None
        
        if delivery_address_id:
            try:
                address = DeliveryAddress.objects.get(id=delivery_address_id, user=user)
            except DeliveryAddress.DoesNotExist:
                address = None
        else:
            address = DeliveryAddress.objects.filter(user=user, is_default=True).first()
        
        if address:
            Delivery.objects.create(
                order=order,
                recipient_name=address.recipient_name,
                recipient_phone=address.recipient_phone,
                address_line1=address.address_line1,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                country=address.country,
                postal_code=address.postal_code,
                delivery_status='pending',
                estimated_arrival=timezone.now().date() + timezone.timedelta(days=5)
            )
        else:
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.email
            
            try:
                default_country = Country.objects.first()
                default_state = State.objects.filter(country=default_country).first()
                default_city = City.objects.filter(state=default_state).first()
                
                Delivery.objects.create(
                    order=order,
                    recipient_name=recipient_name,
                    recipient_phone=user.phone or "",
                    address_line1="Pendiente de confirmar",
                    city=default_city,
                    state=default_state,
                    country=default_country,
                    delivery_status='pending',
                    delivery_notes="Confirmar dirección de entrega"
                )
            except Exception:
                pass
    except Exception:
        pass