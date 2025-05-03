from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
from django.conf import settings
from django.core.files.base import ContentFile
from uuid import uuid4

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from core.models import LoggerService
from core.pagination import CustomPagination

from .models import Report
from .serializers import ReportSerializer, ReportCreateSerializer
from app.orders.models import Order, OrderItem, Payment
from app.products.models import Product, Inventory
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

@extend_schema(tags=['Report'])
class ReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    @extend_schema(
        summary='Get all reports',
        description='Retrieves a paginated list of reports. Staff users can see all reports, while regular users only see their own reports.',
        responses={
            200: ReportSerializer(many=True),
            500: OpenApiResponse(description='Server error'),
        },
        parameters=[
            OpenApiParameter(
                name='page', 
                description='Page number for pagination',
                required=False, 
                type=int
            ),
            OpenApiParameter(
                name='page_size', 
                description='Number of items per page',
                required=False,
                type=int
            )
        ]
    )
    def get(self, request):
        try:
            if request.user.is_staff:
                reports = Report.objects.all().order_by('-created_at')
            else:
                reports = Report.objects.filter(user=request.user).order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_reports = paginator.paginate_queryset(reports, request)
            serializer = ReportSerializer(paginated_reports, many=True)
            
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f"Error retrieving reports: {str(e)}"
            )
            return Response({"detail": "Error retrieving reports"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary='Create a new report',
        description='Generates a new report based on the provided parameters. The report can be of different types and formats.',
        request=ReportCreateSerializer,
        responses={
            200: ReportSerializer,
            400: OpenApiResponse(description='Invalid input'),
            500: OpenApiResponse(description='Server error'),
        },
        examples=[
            OpenApiExample(
                name='Sales by Customer Report',
                summary='Generate a sales by customer report',
                description='Creates a report showing sales data organized by customer',
                value={
                    "name": "Monthly Sales by Customer",
                    "report_type": "sales_by_customer",
                    "format": "pdf",
                    "start_date": "2025-03-26",
                    "end_date": "2025-04-26",
                    "language": "en"
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Best Sellers Report',
                summary='Generate a best sellers report',
                description='Creates a report showing the best selling products',
                value={
                    "name": "Best Sellers Q1",
                    "report_type": "best_sellers",
                    "format": "excel",
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31",
                    "language": "es"
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Sales by Period Report',
                summary='Generate a sales by period report',
                description='Creates a report showing sales data organized by time periods',
                value={
                    "name": "Weekly Sales Report",
                    "report_type": "sales_by_period",
                    "format": "pdf",
                    "start_date": "2025-04-19",
                    "end_date": "2025-04-26",
                    "language": "en"
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Product Performance Report',
                summary='Generate a product performance report',
                description='Creates a report analyzing product performance including profit margins',
                value={
                    "name": "Product Performance Analysis",
                    "report_type": "product_performance",
                    "format": "excel",
                    "start_date": "2025-03-01",
                    "end_date": "2025-04-26",
                    "language": "es"
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Inventory Status Report',
                summary='Generate an inventory status report',
                description='Creates a report showing current inventory levels and status',
                value={
                    "name": "Current Inventory Status",
                    "report_type": "inventory_status",
                    "format": "pdf",
                    "language": "en"
                },
                request_only=True,
            ),
            OpenApiExample(
                name='My Orders Report',
                summary='Generate a personal orders report',
                description='Creates a report showing all your orders with payment and delivery status',
                value={
                    "name": "My Purchase History",
                    "report_type": "my_orders",
                    "format": "pdf",
                    "start_date": "2025-01-01",
                    "end_date": "2025-04-30",
                    "language": "en"
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Order Receipt',
                summary='Generate an order receipt',
                description='Creates a detailed receipt for a specific order',
                value={
                    "name": "Order Receipt #1234",
                    "report_type": "order_receipt",
                    "format": "pdf",
                    "language": "en",
                    "order_id": 1234
                },
                request_only=True,
            ),
        ]
    )
    def post(self, request):
        with transaction.atomic():
            try:
                if not request.user.is_authenticated:
                    return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
                
                serializer = ReportCreateSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                report_obj = serializer.save(user=request.user)
                
                data = None
                if report_obj.report_type == 'sales_by_customer':
                    if not request.user.is_staff:
                        return Response({"detail": "Staff permission required for this report type"}, status=status.HTTP_403_FORBIDDEN)
                    data = self.generate_sales_by_customer_data(report_obj)
                elif report_obj.report_type == 'best_sellers':
                    if not request.user.is_staff:
                        return Response({"detail": "Staff permission required for this report type"}, status=status.HTTP_403_FORBIDDEN)
                    data = self.generate_best_sellers_data(report_obj)
                elif report_obj.report_type == 'sales_by_period':
                    if not request.user.is_staff:
                        return Response({"detail": "Staff permission required for this report type"}, status=status.HTTP_403_FORBIDDEN)
                    data = self.generate_sales_by_period_data(report_obj)
                elif report_obj.report_type == 'product_performance':
                    if not request.user.is_staff:
                        return Response({"detail": "Staff permission required for this report type"}, status=status.HTTP_403_FORBIDDEN)
                    data = self.generate_product_performance_data(report_obj)
                elif report_obj.report_type == 'inventory_status':
                    if not request.user.is_staff:
                        return Response({"detail": "Staff permission required for this report type"}, status=status.HTTP_403_FORBIDDEN)
                    data = self.generate_inventory_status_data(report_obj)
                elif report_obj.report_type == 'my_orders':
                    data = self.generate_my_orders_data(report_obj)
                elif report_obj.report_type == 'order_receipt':
                    order_id = serializer.initial_data.get('order_id')
                    if not order_id:
                        return Response({"detail": "Order ID is required for order receipt"}, status=status.HTTP_400_BAD_REQUEST)
                    data = self.generate_order_receipt(report_obj, order_id)
                else:
                    return Response({"detail": "Unknown report type"}, status=400)
                
                report_obj.report_data = data
                
                if report_obj.format == 'pdf':
                    pdf_bytes = self.generate_pdf_content(report_obj)
                    filename = f"{report_obj.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    report_obj.file_path.save(filename, ContentFile(pdf_bytes))
                    
                elif report_obj.format == 'excel':
                    excel_bytes = self.generate_excel_content(report_obj)
                    filename = f"{report_obj.report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    report_obj.file_path.save(filename, ContentFile(excel_bytes))
                
                report_obj.save()
                
                return Response(ReportSerializer(report_obj).data, status=status.HTTP_200_OK)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Report',
                    description=f"Error creating report: {str(e)}"
                )
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_translated_text(self, report, text_en):
        translations = {
            'en': {
                'Order ID': 'Order ID',
                'Customer': 'Customer',
                'Total Amount': 'Total Amount',
                'Currency': 'Currency',
                'Date': 'Date',
                'Product ID': 'Product ID',
                'Product Name': 'Product Name',
                'Quantity Sold': 'Quantity Sold',
                'Revenue': 'Revenue',
                'Period': 'Period',
                'Orders': 'Orders',
                'Sales': 'Sales',
                'Profit': 'Profit',
                'Profit Margin': 'Profit Margin',
                'Current Stock': 'Current Stock',
                'Reorder Level': 'Reorder Level',
                'Status': 'Status',
                'Count': 'Count',
                'Low Stock': 'Low Stock',
                'In Stock': 'In Stock',
                'Out of Stock': 'Out of Stock',
                'Report Date': 'Report Date',
                'Date Range': 'Date Range',
                'Generated by': 'Generated by',
                'Page': 'Page',
                'Summary': 'Summary',
                'Sales by Customer': 'Sales by Customer',
                'Best Sellers': 'Best Sellers',
                'Sales by Period': 'Sales by Period',
                'Product Performance': 'Product Performance',
                'Inventory Status': 'Inventory Status',
                'My Orders': 'My Orders',
                'All Orders': 'All Orders',
                'Payment Status': 'Payment Status',
                'Delivery Status': 'Delivery Status',
                'Pending': 'Pending',
                'Processing': 'Processing',
                'Completed': 'Completed',
                'Failed': 'Failed',
                'Refunded': 'Refunded',
                'Shipped': 'Shipped',
                'Out_for_delivery': 'Out for Delivery',
                'Delivered': 'Delivered',
                'Returned': 'Returned',
                'Total Spent': 'Total Spent',
                'Cost': 'Cost',
                'Product Code': 'Product Code',
                'USD': 'USD',
                'BS': 'BS',
                'Order Receipt': 'Order Receipt',
                'Order': 'Order',
                'Order Information': 'Order Information',
                'Order Items': 'Order Items',
                'Order Summary': 'Order Summary',
                'Order Date:': 'Order Date:',
                'Customer:': 'Customer:',
                'Email:': 'Email:',
                'Shipping Address:': 'Shipping Address:',
                'Payment Status:': 'Payment Status:',
                'Delivery Status:': 'Delivery Status:',
                'Product': 'Product',
                'Unit Price': 'Unit Price',
                'Quantity': 'Quantity',
                'Total': 'Total',
                'Subtotal:': 'Subtotal:',
                'Shipping:': 'Shipping:',
                'Taxes:': 'Taxes:',
                'Discount:': 'Discount:'
            },
            'es': {
                'Order ID': 'ID de Orden',
                'Customer': 'Cliente',
                'Total Amount': 'Monto Total',
                'Currency': 'Moneda',
                'Date': 'Fecha',
                'Product ID': 'ID de Producto',
                'Product Name': 'Nombre del Producto',
                'Quantity Sold': 'Cantidad Vendida',
                'Revenue': 'Ingresos',
                'Period': 'Período',
                'Orders': 'Órdenes',
                'Sales': 'Ventas',
                'Profit': 'Ganancia',
                'Profit Margin': 'Margen de Ganancia',
                'Current Stock': 'Stock Actual',
                'Reorder Level': 'Nivel de Reorden',
                'Status': 'Estado',
                'Count': 'Cantidad',
                'Low Stock': 'Stock Bajo',
                'In Stock': 'En Stock',
                'Out of Stock': 'Agotado',
                'Report Date': 'Fecha del Informe',
                'Date Range': 'Rango de Fechas',
                'Generated by': 'Generado por',
                'Page': 'Página',
                'Summary': 'Resumen',
                'Sales by Customer': 'Ventas por Cliente',
                'Best Sellers': 'Más Vendidos',
                'Sales by Period': 'Ventas por Período',
                'Product Performance': 'Rendimiento de Productos',
                'Inventory Status': 'Estado de Inventario',
                'My Orders': 'Mis Órdenes',
                'All Orders': 'Todas las Órdenes',
                'Payment Status': 'Estado de Pago',
                'Delivery Status': 'Estado de Entrega',
                'Pending': 'Pendiente',
                'Processing': 'Procesando',
                'Completed': 'Completado',
                'Failed': 'Fallido',
                'Refunded': 'Reembolsado',
                'Shipped': 'Enviado',
                'Out_for_delivery': 'En reparto',
                'Delivered': 'Entregado',
                'Returned': 'Devuelto',
                'Total Spent': 'Total Gastado',
                'Cost': 'Costo',
                'Product Code': 'Código de Producto',
                'USD': 'USD',
                'BS': 'Bs',
                'Order Receipt': 'Recibo de Orden',
                'Order': 'Orden',
                'Order Information': 'Información de la Orden',
                'Order Items': 'Artículos de la Orden',
                'Order Summary': 'Resumen de la Orden',
                'Order Date:': 'Fecha de la Orden:',
                'Customer:': 'Cliente:',
                'Email:': 'Correo Electrónico:',
                'Shipping Address:': 'Dirección de Envío:',
                'Payment Status:': 'Estado del Pago:',
                'Delivery Status:': 'Estado de la Entrega:',
                'Product': 'Producto',
                'Unit Price': 'Precio Unitario',
                'Quantity': 'Cantidad',
                'Total': 'Total',
                'Subtotal:': 'Subtotal:',
                'Shipping:': 'Envío:',
                'Taxes:': 'Impuestos:',
                'Discount:': 'Descuento:'
            }
        }
        
        lang = report.language if report and report.language in translations else 'en'
        return translations[lang].get(text_en, text_en)
        
    def generate_sales_by_customer_data(self, report):
        start_date = report.start_date or (datetime.now() - timedelta(days=30)).date()
        end_date = report.end_date or datetime.now().date()
        
        orders = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            payment__payment_status='completed'
        ).select_related('user')
        
        headers = [
            self.get_translated_text(report, 'Order ID'),
            self.get_translated_text(report, 'Customer'),
            self.get_translated_text(report, 'Total Amount'),
            self.get_translated_text(report, 'Currency'),
            self.get_translated_text(report, 'Date'),
        ]
        
        rows = []
        customer_totals = {}
        
        for order in orders:
            customer_name = f"{order.user.first_name} {order.user.last_name}" if order.user else "Guest"
            if customer_name not in customer_totals:
                customer_totals[customer_name] = {"USD": 0, "BS": 0}
                
            customer_totals[customer_name][order.currency] += float(order.total_amount)
            
            rows.append({
                headers[0]: order.id,
                headers[1]: customer_name,
                headers[2]: float(order.total_amount),
                headers[3]: order.currency,
                headers[4]: order.created_at.strftime('%Y-%m-%d')
            })
        
        summary = []
        for customer, totals in sorted(customer_totals.items(), key=lambda x: sum(x[1].values()), reverse=True):
            for currency, amount in totals.items():
                if amount > 0:
                    summary.append({
                        self.get_translated_text(report, 'Customer'): customer,
                        self.get_translated_text(report, 'Total Amount'): amount,
                        self.get_translated_text(report, 'Currency'): currency
                    })
            
        return {
            'title': self.get_translated_text(report, 'Sales by Customer'),
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows,
            'summary': summary
        }
    
    def generate_best_sellers_data(self, report):
        start_date = report.start_date or (datetime.now() - timedelta(days=30)).date()
        end_date = report.end_date or datetime.now().date()
        
        completed_orders = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            payment__payment_status='completed'
        )
        
        order_ids = completed_orders.values_list('id', flat=True)
        
        items = OrderItem.objects.filter(order_id__in=order_ids).select_related('order', 'product')
        
        headers = [
            self.get_translated_text(report, 'Product ID'),
            self.get_translated_text(report, 'Product Name'),
            self.get_translated_text(report, 'Quantity Sold'),
            self.get_translated_text(report, 'Revenue'),
            self.get_translated_text(report, 'Currency')
        ]
        
        product_stats = {}
        
        for item in items:
            if not item.product:
                continue
                
            product_id = item.product_id
            product_name = item.product.name
            currency = item.order.currency
            
            if product_id not in product_stats:
                product_stats[product_id] = {
                    'name': product_name,
                    'quantity': 0,
                    'revenue': {"USD": 0, "BS": 0}
                }
            
            product_stats[product_id]['quantity'] += item.quantity
            
            total_price = getattr(item, 'total_price', None)
            if total_price is None and hasattr(item.product, 'price'):
                total_price = item.product.price * item.quantity
            elif total_price is None:
                total_price = 0
                
            product_stats[product_id]['revenue'][currency] += float(total_price)
        
        sorted_products = sorted(
            product_stats.items(), 
            key=lambda x: x[1]['quantity'], 
            reverse=True
        )
        
        rows = []
        for product_id, stats in sorted_products:
            for currency in ['USD', 'BS']:
                if stats['revenue'][currency] > 0:
                    rows.append({
                        headers[0]: product_id,
                        headers[1]: stats['name'],
                        headers[2]: stats['quantity'],
                        headers[3]: stats['revenue'][currency],
                        headers[4]: currency
                    })
        
        return {
            'title': self.get_translated_text(report, 'Best Sellers'),
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows
        }

    def generate_sales_by_period_data(self, report):
        start_date = report.start_date or (datetime.now() - timedelta(days=30)).date()
        end_date = report.end_date or datetime.now().date()
        
        orders = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            payment__payment_status='completed'
        ).select_related('payment')
        
        headers = [
            self.get_translated_text(report, 'Period'),
            self.get_translated_text(report, 'Orders'),
            self.get_translated_text(report, 'Sales'),
            self.get_translated_text(report, 'Currency')
        ]
        
        daily_sales = {}
        
        for order in orders:
            date_str = order.created_at.date().strftime('%Y-%m-%d')
            if date_str not in daily_sales:
                daily_sales[date_str] = {
                    'USD': {'count': 0, 'total': 0},
                    'BS': {'count': 0, 'total': 0}
                }
            
            currency = order.currency
            daily_sales[date_str][currency]['count'] += 1
            daily_sales[date_str][currency]['total'] += float(order.total_amount)
        
        rows = []
        for date_str, currencies in sorted(daily_sales.items()):
            for currency, data in currencies.items():
                if data['count'] > 0:
                    rows.append({
                        headers[0]: date_str,
                        headers[1]: data['count'],
                        headers[2]: data['total'],
                        headers[3]: currency
                    })
        
        total_by_currency = {'USD': {'orders': 0, 'sales': 0}, 'BS': {'orders': 0, 'sales': 0}}
        for date_data in daily_sales.values():
            for currency, data in date_data.items():
                total_by_currency[currency]['orders'] += data['count']
                total_by_currency[currency]['sales'] += data['total']
        
        summary = []
        for currency, totals in total_by_currency.items():
            if totals['orders'] > 0:
                summary.append({
                    self.get_translated_text(report, 'Currency'): currency,
                    self.get_translated_text(report, 'Orders'): totals['orders'],
                    self.get_translated_text(report, 'Sales'): totals['sales']
                })
        
        return {
            'title': self.get_translated_text(report, 'Sales by Period'),
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows,
            'summary': summary
        }
        
    def generate_product_performance_data(self, report):
        start_date = report.start_date or (datetime.now() - timedelta(days=30)).date()
        end_date = report.end_date or datetime.now().date()
        
        completed_orders = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            payment__payment_status='completed'
        )
        
        order_ids = completed_orders.values_list('id', flat=True)
        items = OrderItem.objects.filter(order_id__in=order_ids).select_related('product', 'order')
        
        headers = [
            self.get_translated_text(report, 'Product ID'),
            self.get_translated_text(report, 'Product Name'),
            self.get_translated_text(report, 'Quantity Sold'),
            self.get_translated_text(report, 'Revenue'),
            self.get_translated_text(report, 'Currency')
        ]
        
        product_performance = {}
        
        for item in items:
            if not item.product:
                continue
                
            product_id = item.product.id
            product_name = item.product.name
            currency = item.order.currency
            
            if product_id not in product_performance:
                product_performance[product_id] = {
                    'name': product_name,
                    'quantity': 0,
                    'revenue': {"USD": 0, "BS": 0},
                }
            
            total_price = getattr(item, 'total_price', None)
            if total_price is None and hasattr(item.product, 'price'):
                total_price = item.product.price * item.quantity
            elif total_price is None:
                total_price = 0
                
            product_performance[product_id]['quantity'] += item.quantity
            product_performance[product_id]['revenue'][currency] += float(total_price)
        
        rows = []
        for product_id, data in sorted(product_performance.items(), key=lambda x: sum(x[1]['revenue'].values()), reverse=True):
            for currency in ['USD', 'BS']:
                if data['revenue'][currency] > 0:
                    rows.append({
                        headers[0]: product_id,
                        headers[1]: data['name'],
                        headers[2]: data['quantity'],
                        headers[3]: data['revenue'][currency],
                        headers[4]: currency
                    })
        
        return {
            'title': self.get_translated_text(report, 'Product Performance'),
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows
        }

    def generate_inventory_status_data(self, report):
        inventory_items = Inventory.objects.all().select_related('product')
        
        headers = [
            self.get_translated_text(report, 'Product ID'),
            self.get_translated_text(report, 'Product Name'),
            self.get_translated_text(report, 'Current Stock'),
            self.get_translated_text(report, 'Status')
        ]
        
        rows = []
        status_counts = {
            'low_stock': 0,
            'in_stock': 0,
            'out_of_stock': 0
        }
        
        for inventory in inventory_items:
            if not inventory.product:
                continue
                
            current_stock = inventory.stock if hasattr(inventory, 'stock') else 0
            reorder_level = inventory.reorder_level if hasattr(inventory, 'reorder_level') else 10
            
            if current_stock <= 0:
                status = self.get_translated_text(report, 'Out of Stock')
                status_counts['out_of_stock'] += 1
            elif current_stock <= reorder_level:
                status = self.get_translated_text(report, 'Low Stock')
                status_counts['low_stock'] += 1
            else:
                status = self.get_translated_text(report, 'In Stock')
                status_counts['in_stock'] += 1
            
            rows.append({
                headers[0]: inventory.product.id,
                headers[1]: inventory.product.name,
                headers[2]: current_stock,
                headers[3]: status
            })
        
        rows.sort(key=lambda x: x[headers[2]])
        
        summary = [
            {
                self.get_translated_text(report, 'Status'): self.get_translated_text(report, 'Out of Stock'),
                self.get_translated_text(report, 'Count'): status_counts['out_of_stock']
            },
            {
                self.get_translated_text(report, 'Status'): self.get_translated_text(report, 'Low Stock'),
                self.get_translated_text(report, 'Count'): status_counts['low_stock']
            },
            {
                self.get_translated_text(report, 'Status'): self.get_translated_text(report, 'In Stock'),
                self.get_translated_text(report, 'Count'): status_counts['in_stock']
            }
        ]
        
        return {
            'title': self.get_translated_text(report, 'Inventory Status'),
            'headers': headers,
            'rows': rows,
            'summary': summary
        }

    def generate_my_orders_data(self, report):
        start_date = report.start_date or (datetime.now() - timedelta(days=90)).date()
        end_date = report.end_date or datetime.now().date()
        
        if report.user.is_staff:
            orders = Order.objects.filter(
                created_at__date__range=[start_date, end_date],
            ).select_related('payment', 'user').order_by('-created_at')
            title = self.get_translated_text(report, 'All Orders')
        else:
            orders = Order.objects.filter(
                user=report.user,
                created_at__date__range=[start_date, end_date],
            ).select_related('payment').order_by('-created_at')
            title = self.get_translated_text(report, 'My Orders')
        
        headers = [
            self.get_translated_text(report, 'Order ID'),
            self.get_translated_text(report, 'Date'),
        ]
        
        if report.user.is_staff:
            headers.insert(1, self.get_translated_text(report, 'Customer'))
            
        headers.extend([
            self.get_translated_text(report, 'Total Amount'),
            self.get_translated_text(report, 'Currency'),
            self.get_translated_text(report, 'Payment Status'),
            self.get_translated_text(report, 'Delivery Status')
        ])
        
        rows = []
        total_by_currency = {'USD': 0, 'BS': 0}
        customer_totals = {}
        
        for order in orders:
            payment_status = 'pending'
            delivery_status = 'pending'
            
            if hasattr(order, 'payment'):
                payment_status = order.payment.payment_status
                
            if hasattr(order, 'delivery'):
                delivery_status = order.delivery.delivery_status
            
            row_data = {
                headers[0]: order.id,
                headers[-5]: order.created_at.strftime('%Y-%m-%d %H:%M'),
                headers[-4]: float(order.total_amount),
                headers[-3]: order.currency,
                headers[-2]: self.get_translated_text(report, payment_status.capitalize()),
                headers[-1]: self.get_translated_text(report, delivery_status.capitalize())
            }
            
            if report.user.is_staff:
                customer_name = f"{order.user.first_name} {order.user.last_name}" if order.user else "Guest"
                row_data[headers[1]] = customer_name
                
                if customer_name not in customer_totals:
                    customer_totals[customer_name] = {"USD": 0, "BS": 0}
                
                if hasattr(order, 'payment') and order.payment.payment_status == 'completed':
                    customer_totals[customer_name][order.currency] += float(order.total_amount)
            
            rows.append(row_data)
            
            if hasattr(order, 'payment') and order.payment.payment_status == 'completed':
                total_by_currency[order.currency] += float(order.total_amount)
        
        summary = []
        
        if report.user.is_staff and customer_totals:
            for customer, totals in sorted(customer_totals.items(), key=lambda x: sum(x[1].values()), reverse=True):
                for currency, amount in totals.items():
                    if amount > 0:
                        summary.append({
                            self.get_translated_text(report, 'Customer'): customer,
                            self.get_translated_text(report, 'Total Amount'): amount,
                            self.get_translated_text(report, 'Currency'): currency
                        })
        
        for currency, total in total_by_currency.items():
            if total > 0:
                summary.append({
                    self.get_translated_text(report, 'Currency'): currency,
                    self.get_translated_text(report, 'Total Spent'): total
                })
        
        return {
            'title': title,
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows,
            'summary': summary
        }
        
    def generate_order_receipt(self, report, order_id):
        try:
            if report.user.is_staff:
                order = Order.objects.get(id=order_id)
            else:
                order = Order.objects.get(id=order_id, user=report.user)
                
            order_items = OrderItem.objects.filter(order=order).select_related('product')
            
            customer_name = f"{order.user.first_name} {order.user.last_name}" if order.user else "Guest"
            customer_email = order.user.email if order.user else ""
            
            shipping_address = ""
            delivery = None
            
            if hasattr(order, 'delivery') and order.delivery:
                delivery = order.delivery
                address_parts = []
                for field in ['address', 'city', 'state', 'country', 'postal_code']:
                    if hasattr(delivery, field) and getattr(delivery, field):
                        address_parts.append(str(getattr(delivery, field)))
                shipping_address = ", ".join(address_parts)
            
            payment_status = "Pending"
            if hasattr(order, 'payment') and order.payment:
                payment_status = order.payment.payment_status.capitalize()
                
            delivery_status = "Pending"
            if delivery:
                delivery_status = delivery.delivery_status.capitalize() if hasattr(delivery, 'delivery_status') else "Pending"
                
            order_info = {
                'order_id': order.id,
                'order_date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                'customer': customer_name,
                'email': customer_email,
                'shipping_address': shipping_address,
                'payment_status': self.get_translated_text(report, payment_status),
                'delivery_status': self.get_translated_text(report, delivery_status),
                'subtotal': float(order.total_amount),
                'shipping_fee': 0,
                'taxes': 0,
                'discount': 0,
                'total': float(order.total_amount),
                'currency': order.currency
            }
            
            # Try to get more detailed financial info if available
            if hasattr(order, 'subtotal'):
                order_info['subtotal'] = float(order.subtotal)
            if hasattr(order, 'shipping_fee'):
                order_info['shipping_fee'] = float(order.shipping_fee)
            if hasattr(order, 'tax_amount'):
                order_info['taxes'] = float(order.tax_amount)
            if hasattr(order, 'discount_amount'):
                order_info['discount'] = float(order.discount_amount)
            
            items_headers = [
                self.get_translated_text(report, 'Product'),
                self.get_translated_text(report, 'Quantity'),
                self.get_translated_text(report, 'Total')
            ]
            
            items_rows = []
            for item in order_items:
                product_name = item.product.name if item.product else f"Product {item.product_id}"
                
                total_price = getattr(item, 'total_price', None)
                if total_price is None and hasattr(item.product, 'price'):
                    total_price = item.product.price * item.quantity
                elif total_price is None:
                    total_price = 0
                
                items_rows.append({
                    items_headers[0]: product_name,
                    items_headers[1]: item.quantity,
                    items_headers[2]: float(total_price)
                })
                
            return {
                'title': self.get_translated_text(report, 'Order Receipt'),
                'subtitle': f"{self.get_translated_text(report, 'Order')} #{order.id}",
                'order': order_info,
                'items_headers': items_headers,
                'items': items_rows
            }
        except Order.DoesNotExist:
            raise Exception("Order not found or you don't have permission to access this order")
        
    def generate_pdf_content(self, report_obj):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        subtitle_style = styles["Heading2"]
        normal_style = styles["Normal"]
        bold_style = styles["Heading4"]
        
        title = report_obj.report_data.get('title', report_obj.name)
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        if report_obj.report_type == 'order_receipt':
            subtitle = report_obj.report_data.get('subtitle', '')
            if subtitle:
                elements.append(Paragraph(subtitle, subtitle_style))
                elements.append(Spacer(1, 12))
            
            order = report_obj.report_data.get('order', {})
            if order:
                elements.append(Paragraph(self.get_translated_text(report_obj, 'Order Information'), bold_style))
                elements.append(Spacer(1, 8))
                
                customer_info = [
                    [self.get_translated_text(report_obj, 'Order Date:'), order.get('order_date', '')],
                    [self.get_translated_text(report_obj, 'Customer:'), order.get('customer', '')],
                    [self.get_translated_text(report_obj, 'Email:'), order.get('email', '')],
                ]
                
                if order.get('shipping_address'):
                    customer_info.append([self.get_translated_text(report_obj, 'Shipping Address:'), 
                                        order.get('shipping_address', '')])
                    
                customer_table = Table(customer_info, colWidths=[120, 300])
                customer_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(customer_table)
                elements.append(Spacer(1, 12))
                
                status_info = [
                    [self.get_translated_text(report_obj, 'Payment Status:'), order.get('payment_status', '')],
                    [self.get_translated_text(report_obj, 'Delivery Status:'), order.get('delivery_status', '')],
                ]
                
                status_table = Table(status_info, colWidths=[120, 300])
                status_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(status_table)
                elements.append(Spacer(1, 20))
                
                elements.append(Paragraph(self.get_translated_text(report_obj, 'Order Items'), bold_style))
                elements.append(Spacer(1, 8))
                
                items_headers = report_obj.report_data.get('items_headers', [])
                items = report_obj.report_data.get('items', [])
                
                if items_headers and items:
                    data = [items_headers]
                    for item in items:
                        data.append([item.get(h, "") for h in items_headers])
                    
                    items_table = Table(data, repeatRows=1)
                    items_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('ALIGN', (-2, 1), (-2, -1), 'RIGHT'),
                        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    elements.append(items_table)
                    elements.append(Spacer(1, 20))
                
                elements.append(Paragraph(self.get_translated_text(report_obj, 'Order Summary'), bold_style))
                elements.append(Spacer(1, 8))
                
                currency = order.get('currency', '')
                summary_info = [
                    [self.get_translated_text(report_obj, 'Subtotal:'), f"{order.get('subtotal', 0)} {currency}"],
                ]
                
                if order.get('shipping_fee', 0) > 0:
                    summary_info.append([self.get_translated_text(report_obj, 'Shipping:'), 
                                      f"{order.get('shipping_fee', 0)} {currency}"])
                
                if order.get('taxes', 0) > 0:
                    summary_info.append([self.get_translated_text(report_obj, 'Taxes:'), 
                                      f"{order.get('taxes', 0)} {currency}"])
                
                if order.get('discount', 0) > 0:
                    summary_info.append([self.get_translated_text(report_obj, 'Discount:'), 
                                      f"-{order.get('discount', 0)} {currency}"])
                
                summary_info.append([self.get_translated_text(report_obj, 'Total:'), 
                                  f"{order.get('total', 0)} {currency}"])
                
                summary_table = Table(summary_info, colWidths=[120, 100])
                summary_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
                    ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(summary_table)
        else:
            date_range = report_obj.report_data.get('date_range')
            if date_range:
                date_subtitle = f"{self.get_translated_text(report_obj, 'Date Range')}: {date_range}"
                elements.append(Paragraph(date_subtitle, subtitle_style))
                elements.append(Spacer(1, 12))
            
            headers = report_obj.report_data.get('headers', [])
            rows = report_obj.report_data.get('rows', [])
            
            if headers and rows:
                data = [headers]
                for row_dict in rows:
                    data.append([row_dict.get(h, "") for h in headers])
                
                table = Table(data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 24))
            
            summary = report_obj.report_data.get('summary', [])
            if summary:
                elements.append(Paragraph(self.get_translated_text(report_obj, 'Summary'), subtitle_style))
                elements.append(Spacer(1, 12))
                
                summary_headers = set()
                for item in summary:
                    summary_headers.update(item.keys())
                summary_headers = list(summary_headers)
                
                summary_data = [summary_headers]
                for item in summary:
                    summary_data.append([item.get(h, "") for h in summary_headers])
                
                summary_table = Table(summary_data, repeatRows=1)
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(summary_table)
        
        elements.append(Spacer(1, 48))
        footer_text = f"{self.get_translated_text(report_obj, 'Report Date')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if report_obj.user:
            footer_text += f", {self.get_translated_text(report_obj, 'Generated by')}: {report_obj.user.first_name} {report_obj.user.last_name}"
        elements.append(Paragraph(footer_text, normal_style))
        
        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _header_footer(self, canvas, doc):
        canvas.saveState()
        
        header_text = "FICCT E-Commerce"
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawString(72, 800, header_text)
        
        canvas.setFont('Helvetica', 9)
        page_text = f"{self.get_translated_text(None, 'Page')} {doc.page}"
        canvas.drawString(72, 30, page_text)
        
        canvas.restoreState()
        
    def generate_excel_content(self, report_obj):
        wb = Workbook()
        ws = wb.active
        ws.title = report_obj.report_type[:31]
        
        ws['A1'] = report_obj.report_data.get('title', report_obj.name)
        ws.merge_cells('A1:E1')
        title_cell = ws['A1']
        title_cell.font = Font(size=16, bold=True)
        
        if report_obj.report_type == 'order_receipt':
            subtitle = report_obj.report_data.get('subtitle', '')
            if subtitle:
                ws['A2'] = subtitle
                ws.merge_cells('A2:E2')
                ws['A2'].font = Font(size=14, bold=True)
            
            order = report_obj.report_data.get('order', {})
            row_idx = 4
            
            if order:
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Order Information'))
                ws.cell(row=row_idx, column=1).font = Font(size=14, bold=True)
                row_idx += 2
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Order Date:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=order.get('order_date', ''))
                row_idx += 1
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Customer:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=order.get('customer', ''))
                row_idx += 1
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Email:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=order.get('email', ''))
                row_idx += 1
                
                if order.get('shipping_address'):
                    ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Shipping Address:'))
                    ws.cell(row=row_idx, column=1).font = Font(bold=True)
                    ws.cell(row=row_idx, column=2, value=order.get('shipping_address', ''))
                    row_idx += 1
                
                row_idx += 1
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Payment Status:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=order.get('payment_status', ''))
                row_idx += 1
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Delivery Status:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=order.get('delivery_status', ''))
                row_idx += 2
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Order Items'))
                ws.cell(row=row_idx, column=1).font = Font(size=14, bold=True)
                row_idx += 2
                
                items_headers = report_obj.report_data.get('items_headers', [])
                items = report_obj.report_data.get('items', [])
                
                if items_headers and items:
                    for col_idx, header in enumerate(items_headers, 1):
                        cell = ws.cell(row=row_idx, column=col_idx, value=header)
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                    
                    for item in items:
                        row_idx += 1
                        for col_idx, header in enumerate(items_headers, 1):
                            ws.cell(row=row_idx, column=col_idx, value=item.get(header, ""))
                
                row_idx += 2
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Order Summary'))
                ws.cell(row=row_idx, column=1).font = Font(size=14, bold=True)
                row_idx += 2
                
                currency = order.get('currency', '')
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Subtotal:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=f"{order.get('subtotal', 0)} {currency}")
                row_idx += 1
                
                if order.get('shipping_fee', 0) > 0:
                    ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Shipping:'))
                    ws.cell(row=row_idx, column=1).font = Font(bold=True)
                    ws.cell(row=row_idx, column=2, value=f"{order.get('shipping_fee', 0)} {currency}")
                    row_idx += 1
                
                if order.get('taxes', 0) > 0:
                    ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Taxes:'))
                    ws.cell(row=row_idx, column=1).font = Font(bold=True)
                    ws.cell(row=row_idx, column=2, value=f"{order.get('taxes', 0)} {currency}")
                    row_idx += 1
                
                if order.get('discount', 0) > 0:
                    ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Discount:'))
                    ws.cell(row=row_idx, column=1).font = Font(bold=True)
                    ws.cell(row=row_idx, column=2, value=f"-{order.get('discount', 0)} {currency}")
                    row_idx += 1
                
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Total:'))
                ws.cell(row=row_idx, column=1).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=f"{order.get('total', 0)} {currency}")
                ws.cell(row=row_idx, column=2).font = Font(bold=True)
        else:
            date_range = report_obj.report_data.get('date_range')
            if date_range:
                ws['A2'] = f"{self.get_translated_text(report_obj, 'Date Range')}: {date_range}"
                ws.merge_cells('A2:E2')
            
            headers = report_obj.report_data.get('headers', [])
            rows = report_obj.report_data.get('rows', [])
            
            row_idx = 4
            
            if headers and rows:
                for col_idx, header in enumerate(headers, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=header)
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                    
                for row_data in rows:
                    row_idx += 1
                    for col_idx, header in enumerate(headers, 1):
                        ws.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
            
            summary = report_obj.report_data.get('summary', [])
            if summary:
                row_idx += 2
                ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Summary'))
                ws.cell(row=row_idx, column=1).font = Font(size=14, bold=True)
                row_idx += 1
                
                summary_headers = set()
                for item in summary:
                    summary_headers.update(item.keys())
                summary_headers = list(summary_headers)
                
                for col_idx, header in enumerate(summary_headers, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=header)
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                    
                for item in summary:
                    row_idx += 1
                    for col_idx, header in enumerate(summary_headers, 1):
                        ws.cell(row=row_idx, column=col_idx, value=item.get(header, ""))
        
        row_idx += 2
        footer_text = f"{self.get_translated_text(report_obj, 'Report Date')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if report_obj.user:
            footer_text += f", {self.get_translated_text(report_obj, 'Generated by')}: {report_obj.user.first_name} {report_obj.user.last_name}"
        ws.cell(row=row_idx, column=1, value=footer_text)
        
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        buffer = BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()
        buffer.close()
        
        return excel_bytes