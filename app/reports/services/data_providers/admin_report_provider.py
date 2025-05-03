from django.db.models import Sum, Count, F, Q
from datetime import datetime
from app.products.models.product_model import Product
from app.orders.models.order_model import Order
from app.orders.models.order_item_model import OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminReportProvider:
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
    
    def get_sales_by_customer_data(self):
        users = User.objects.filter(is_staff=False)
        
        sales_data = {
            'title': 'Sales by Customer Report' if self.language == 'en' else 'Reporte de Ventas por Cliente',
            'date_range': f"{self.start_date} to {self.end_date}" if self.start_date and self.end_date else "All time",
            'customers': []
        }
        
        total_revenue = 0
        for user in users:
            user_orders = Order.objects.filter(user=user)
            user_orders = self._filter_by_date(user_orders)
            
            user_revenue = user_orders.aggregate(total=Sum('total_amount'))['total'] or 0
            total_revenue += user_revenue
            
            if user_revenue > 0:
                sales_data['customers'].append({
                    'customer_id': user.id,
                    'customer_email': user.email,
                    'orders_count': user_orders.count(),
                    'total_revenue': user_revenue,
                    'first_order_date': user_orders.order_by('created_at').first().created_at if user_orders.exists() else None,
                    'last_order_date': user_orders.order_by('-created_at').first().created_at if user_orders.exists() else None
                })
        
        sales_data['total_revenue'] = total_revenue
        sales_data['total_customers'] = len(sales_data['customers'])
        
        sales_data['customers'] = sorted(
            sales_data['customers'], 
            key=lambda x: x['total_revenue'], 
            reverse=True
        )
        
        return sales_data
    
    def get_best_sellers_data(self):
        order_items = OrderItem.objects.all()
        order_items = self._filter_by_date(order_items, 'order__created_at')
        
        product_sales = {}
        for item in order_items:
            product_id = item.product_id
            
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
            
            if product_id in product_sales:
                product_sales[product_id]['quantity'] += item.quantity
                product_sales[product_id]['revenue'] += unit_price * item.quantity
            else:
                product = item.product
                product_sales[product_id] = {
                    'product_id': product_id,
                    'product_name': product.name,
                    'product_brand': product.brand.name if hasattr(product, 'brand') and product.brand else None,
                    'product_category': product.category.name if hasattr(product, 'category') and product.category else None,
                    'quantity': item.quantity,
                    'revenue': unit_price * item.quantity,
                    'average_rating': product.average_rating if hasattr(product, 'average_rating') else None
                }
        
        products_list = list(product_sales.values())
        products_sorted = sorted(products_list, key=lambda x: x['quantity'], reverse=True)
        
        return {
            'title': 'Best Sellers Report' if self.language == 'en' else 'Reporte de Mejores Vendedores',
            'date_range': f"{self.start_date} to {self.end_date}" if self.start_date and self.end_date else "All time",
            'products': products_sorted[:25],
            'total_products': len(products_sorted)
        }
    
    def get_sales_by_period_data(self):
        orders = Order.objects.all()
        orders = self._filter_by_date(orders)
        
        date_difference = None
        if self.start_date and self.end_date:
            date_difference = (self.end_date - self.start_date).days
        
        group_by = 'month' if date_difference and date_difference > 60 else 'day'
        
        sales_data = {
            'title': 'Sales by Period Report' if self.language == 'en' else 'Reporte de Ventas por Período',
            'date_range': f"{self.start_date} to {self.end_date}" if self.start_date and self.end_date else "All time",
            'group_by': group_by,
            'periods': [],
            'total_revenue': 0,
            'total_orders': 0
        }
        
        if group_by == 'month':
            from django.db.models.functions import TruncMonth
            period_data = orders.annotate(period=TruncMonth('created_at')) \
                .values('period') \
                .annotate(revenue=Sum('total_amount'), count=Count('id')) \
                .order_by('period')
            
            for data in period_data:
                sales_data['periods'].append({
                    'period': data['period'].strftime("%b %Y"),
                    'revenue': float(data['revenue']),
                    'orders_count': data['count']
                })
                sales_data['total_revenue'] += float(data['revenue'])
                sales_data['total_orders'] += data['count']
                
        else:
            from django.db.models.functions import TruncDay
            period_data = orders.annotate(period=TruncDay('created_at')) \
                .values('period') \
                .annotate(revenue=Sum('total_amount'), count=Count('id')) \
                .order_by('period')
            
            for data in period_data:
                sales_data['periods'].append({
                    'period': data['period'].strftime("%Y-%m-%d"),
                    'revenue': float(data['revenue']),
                    'orders_count': data['count']
                })
                sales_data['total_revenue'] += float(data['revenue'])
                sales_data['total_orders'] += data['count']
        
        return sales_data
    
    def get_product_performance_data(self):
        products = Product.objects.all()
        
        performance_data = {
            'title': 'Product Performance Report' if self.language == 'en' else 'Reporte de Rendimiento de Productos',
            'date_range': f"{self.start_date} to {self.end_date}" if self.start_date and self.end_date else "All time",
            'products': []
        }
        
        for product in products:
            order_items = OrderItem.objects.filter(product=product)
            order_items = self._filter_by_date(order_items, 'order__created_at')
            
            total_sold = order_items.aggregate(total=Sum('quantity'))['total'] or 0
            total_revenue = 0
            for item in order_items:
                total_revenue += item.price * item.quantity
            
            if total_sold > 0:
                performance_data['products'].append({
                    'id': product.id,
                    'name': product.name,
                    'brand': product.brand.name if hasattr(product, 'brand') and product.brand else None,
                    'category': product.category.name if hasattr(product, 'category') and product.category else None,
                    'price_usd': float(product.price_usd) if hasattr(product, 'price_usd') and product.price_usd else None,
                    'average_rating': product.average_rating if hasattr(product, 'average_rating') else None,
                    'total_reviews': product.total_reviews if hasattr(product, 'total_reviews') else None,
                    'units_sold': total_sold,
                    'revenue': total_revenue
                })
        
        performance_data['products'] = sorted(
            performance_data['products'], 
            key=lambda x: x['revenue'], 
            reverse=True
        )
        
        return performance_data
    
    def get_inventory_status_data(self):
        products = Product.objects.all()
        
        inventory_data = {
            'title': 'Inventory Status Report' if self.language == 'en' else 'Reporte de Estado de Inventario',
            'date_generated': datetime.now(),
            'total_products': products.count(),
            'active_products': products.filter(active=True).count(),
            'products': []
        }
        
        for product in products:
            order_items = OrderItem.objects.filter(product=product)
            order_items = self._filter_by_date(order_items, 'order__created_at')
            units_sold = order_items.aggregate(total=Sum('quantity'))['total'] or 0
            
            inventory_data['products'].append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand.name if hasattr(product, 'brand') and product.brand else None,
                'category': product.category.name if hasattr(product, 'category') and product.category else None,
                'price_usd': float(product.price_usd) if hasattr(product, 'price_usd') and product.price_usd else None,
                'price_bs': float(product.price_bs) if hasattr(product, 'price_bs') and product.price_bs else None,
                'active': product.active if hasattr(product, 'active') else True,
                'units_sold': units_sold,
                'last_sold': order_items.order_by('-order__created_at').first().order.created_at if order_items.exists() else None
            })
        
        inventory_data['products'] = sorted(
            inventory_data['products'], 
            key=lambda x: x.get('units_sold', 0), 
            reverse=True
        )
        
        return inventory_data
    
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