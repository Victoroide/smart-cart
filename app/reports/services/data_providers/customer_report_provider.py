from django.db.models import Sum, Count
from app.orders.models.order_model import Order
from app.orders.models.order_item_model import OrderItem

class CustomerReportProvider:
    def __init__(self, user, report):
        self.user = user
        self.report = report
        self.start_date = report.start_date
        self.end_date = report.end_date
        self.language = report.language
    
    def _filter_by_date(self, queryset, date_field='created_at'):
        if self.start_date:
            queryset = queryset.filter(**{f'{date_field}__date__gte': self.start_date})
        if self.end_date:
            queryset = queryset.filter(**{f'{date_field}__date__lte': self.end_date})
        return queryset
    
    def get_customer_orders_data(self):
        orders = Order.objects.filter(user=self.user)
        orders = self._filter_by_date(orders)
        
        orders_data = {
            'title': 'My Orders History' if self.language == 'en' else 'Historial de Mis Pedidos',
            'date_range': f"{self.start_date} to {self.end_date}" if self.start_date and self.end_date else "All time",
            'orders': [],
            'status_summary': {}
        }
        
        total_spent = 0
        for order in orders:
            # Obtener estado de pago
            payment_status = "Pending"
            try:
                from app.orders.models.payment_model import Payment
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    payment_status = payment.payment_status
            except Exception:
                pass
            
            # Estado de entrega si existe
            delivery_status = None
            try:
                if hasattr(order, 'delivery'):
                    delivery_status = order.delivery.delivery_status
            except Exception:
                pass
            
            # Contador de estados para el resumen
            status_key = delivery_status or payment_status
            orders_data['status_summary'][status_key] = orders_data['status_summary'].get(status_key, 0) + 1
            
            # Contamos los items
            items = OrderItem.objects.filter(order=order)
            items_count = items.count()
            products_count = items.values('product').distinct().count()
            
            total_spent += order.total_amount
            
            orders_data['orders'].append({
                'id': order.id,
                'date': order.created_at,
                'status': delivery_status or payment_status,  # Usamos el estado de entrega si existe, si no, el de pago
                'items_count': items_count,
                'products_count': products_count,
                'total_amount': float(order.total_amount),
                'currency': order.currency
            })
        
        orders_data['total_orders'] = len(orders_data['orders'])
        orders_data['total_spent'] = float(total_spent)
        
        return orders_data

    def get_order_receipt_data(self, order_id=None):
        if not order_id:
            return {'error': 'Missing parameter', 'message': 'Order ID is required'}
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return {'error': 'Not found', 'message': 'Order not found'}
        
        order_items = OrderItem.objects.filter(order=order)
        
        # Obtener información de pago
        payment_status = "Pending"
        payment_method = "N/A"
        try:
            from app.orders.models.payment_model import Payment
            payment = Payment.objects.filter(order=order).first()
            if payment:
                payment_status = payment.payment_status
                payment_method = payment.payment_type
        except Exception:
            pass

        # Obtener información de envío desde el modelo Delivery
        shipping_address = "N/A"
        try:
            if hasattr(order, 'delivery'):
                shipping_address = order.delivery.full_address()
        except Exception:
            pass
        
        receipt_data = {
            'title': f'Order Receipt #{order.id}' if self.language == 'en' else f'Recibo de Orden #{order.id}',
            'order_id': order.id,
            'order_uuid': str(order.uuid) if hasattr(order, 'uuid') else None,
            'date': order.created_at.isoformat() if order.created_at else None,  # Convertir datetime a string ISO
            'customer': {
                'id': order.user.id,
                'email': order.user.email,
            },
            'status': payment_status,
            'total_amount': float(order.total_amount),
            'currency': order.currency,
            'discount_applied': float(order.discount_applied) if order.discount_applied else 0,
            'discount_percentage': order.discount_percentage,
            'items': [],
            'shipping_address': shipping_address,
            'billing_address': "N/A",
            'payment_method': payment_method,
            'notes': order.delivery.delivery_notes if hasattr(order, 'delivery') and order.delivery.delivery_notes else ""
        }
        
        for item in order_items:
            # Obtener precio de manera segura
            unit_price = 0
            if hasattr(item, 'unit_price'):
                unit_price = item.unit_price
            elif hasattr(item, 'product_price'):
                unit_price = item.product_price
            elif hasattr(item, 'total'):
                unit_price = item.total / item.quantity if item.quantity else 0
            else:
                unit_price = item.product.price_usd if hasattr(item.product, 'price_usd') else 0
            
            receipt_data['items'].append({
                'product_name': item.product.name,
                'product_id': item.product.id,
                'quantity': item.quantity,
                'price': float(unit_price),
                'subtotal': float(unit_price) * item.quantity
            })
        
        return receipt_data