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
            LoggerService.log_error(f"Error getting reports: {str(e)}")
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
        ]
    )
    def post(self, request):
        with transaction.atomic():
            try:
                # Ensure the user is authenticated
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
                LoggerService.log_error(f"Error creating report: {str(e)}")
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
                'SKU': 'SKU',
                'USD': 'USD',
                'BS': 'BS'
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
                'SKU': 'SKU',
                'USD': 'USD',
                'BS': 'Bs'
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
            product_id = item.product_id
            product_name = item.product.name if item.product else f"Product {product_id}"
            currency = item.order.currency
            
            if product_id not in product_stats:
                product_stats[product_id] = {
                    'name': product_name,
                    'quantity': 0,
                    'revenue': {"USD": 0, "BS": 0}
                }
            
            product_stats[product_id]['quantity'] += item.quantity
            product_stats[product_id]['revenue'][currency] += float(item.price * item.quantity)
            
        sorted_products = sorted(
            product_stats.items(), 
            key=lambda x: x[1]['quantity'], 
            reverse=True
        )
        
        rows = []
        for product_id, stats in sorted_products:
            for currency, amount in stats['revenue'].items():
                if amount > 0:
                    rows.append({
                        headers[0]: product_id,
                        headers[1]: stats['name'],
                        headers[2]: stats['quantity'],
                        headers[3]: amount,
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
        
        payments = Payment.objects.filter(
            created_at__date__range=[start_date, end_date],
            payment_status='completed'
        ).select_related('order')
        
        headers = [
            self.get_translated_text(report, 'Period'),
            self.get_translated_text(report, 'Orders'),
            self.get_translated_text(report, 'Sales'),
            self.get_translated_text(report, 'Currency')
        ]
        
        daily_sales = {}
        for payment in payments:
            if not payment.order:
                continue
                
            date_str = payment.created_at.date().strftime('%Y-%m-%d')
            if date_str not in daily_sales:
                daily_sales[date_str] = {
                    'USD': {'count': 0, 'total': 0},
                    'BS': {'count': 0, 'total': 0}
                }
            
            currency = payment.order.currency
            daily_sales[date_str][currency]['count'] += 1
            daily_sales[date_str][currency]['total'] += float(payment.amount)
            
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
                
        return {
            'title': self.get_translated_text(report, 'Sales by Period'),
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows
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
            self.get_translated_text(report, 'SKU'),
            self.get_translated_text(report, 'Quantity Sold'),
            self.get_translated_text(report, 'Revenue'),
            self.get_translated_text(report, 'Cost'),
            self.get_translated_text(report, 'Profit'),
            self.get_translated_text(report, 'Profit Margin'),
            self.get_translated_text(report, 'Currency')
        ]
        
        product_performance = {}
        
        for item in items:
            if not item.product:
                continue
                
            product_id = item.product.id
            product_name = item.product.name
            sku = item.product.sku
            currency = item.order.currency
            cost = item.product.cost_price
            sold_price = item.price
            quantity = item.quantity
            
            if product_id not in product_performance:
                product_performance[product_id] = {
                    'name': product_name,
                    'sku': sku,
                    'quantity': 0,
                    'revenue': {"USD": 0, "BS": 0},
                    'cost': {"USD": 0, "BS": 0},
                    'profit': {"USD": 0, "BS": 0},
                }
            
            revenue = float(sold_price * quantity)
            cost_total = float(cost * quantity if cost else 0)
            profit = revenue - cost_total
            
            product_performance[product_id]['quantity'] += quantity
            product_performance[product_id]['revenue'][currency] += revenue
            product_performance[product_id]['cost'][currency] += cost_total
            product_performance[product_id]['profit'][currency] += profit
        
        rows = []
        for product_id, data in sorted(product_performance.items(), key=lambda x: sum(x[1]['profit'].values()), reverse=True):
            for currency in ['USD', 'BS']:
                if data['revenue'][currency] > 0:
                    profit_margin = (data['profit'][currency] / data['revenue'][currency]) * 100 if data['revenue'][currency] > 0 else 0
                    
                    rows.append({
                        headers[0]: product_id,
                        headers[1]: data['name'],
                        headers[2]: data['sku'],
                        headers[3]: data['quantity'],
                        headers[4]: data['revenue'][currency],
                        headers[5]: data['cost'][currency],
                        headers[6]: data['profit'][currency],
                        headers[7]: f"{profit_margin:.2f}%",
                        headers[8]: currency
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
            self.get_translated_text(report, 'SKU'),
            self.get_translated_text(report, 'Current Stock'),
            self.get_translated_text(report, 'Reorder Level'),
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
                
            current_stock = inventory.quantity
            reorder_level = inventory.reorder_level or 10
            
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
                headers[2]: inventory.product.sku,
                headers[3]: current_stock,
                headers[4]: reorder_level,
                headers[5]: status
            })
        
        # Sort by remaining stock (ascending)
        rows.sort(key=lambda x: x[headers[3]])
        
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
        
        # Check if user is admin to show all orders or just user's orders
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
        
        # Add Customer column only for admin reports
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
            
            # Add customer info for admin reports
            if report.user.is_staff:
                customer_name = f"{order.user.first_name} {order.user.last_name}" if order.user else "Guest"
                row_data[headers[1]] = customer_name
                
                # Track totals by customer for admin
                if customer_name not in customer_totals:
                    customer_totals[customer_name] = {"USD": 0, "BS": 0}
                
                if hasattr(order, 'payment') and order.payment.payment_status == 'completed':
                    customer_totals[customer_name][order.currency] += float(order.total_amount)
            
            rows.append(row_data)
            
            if hasattr(order, 'payment') and order.payment.payment_status == 'completed':
                total_by_currency[order.currency] += float(order.total_amount)
        
        summary = []
        
        # Add customer breakdown for admin reports
        if report.user.is_staff and customer_totals:
            for customer, totals in sorted(customer_totals.items(), key=lambda x: sum(x[1].values()), reverse=True):
                for currency, amount in totals.items():
                    if amount > 0:
                        summary.append({
                            self.get_translated_text(report, 'Customer'): customer,
                            self.get_translated_text(report, 'Total Amount'): amount,
                            self.get_translated_text(report, 'Currency'): currency
                        })
        
        # Add overall total
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
        
    def generate_pdf_content(self, report_obj):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        subtitle_style = styles["Heading2"]
        normal_style = styles["Normal"]
        
        # Title
        title = report_obj.report_data.get('title', report_obj.name)
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        # Date range if available
        date_range = report_obj.report_data.get('date_range')
        if date_range:
            date_subtitle = f"{self.get_translated_text(report_obj, 'Date Range')}: {date_range}"
            elements.append(Paragraph(date_subtitle, subtitle_style))
            elements.append(Spacer(1, 12))
        
        # Report data
        headers = report_obj.report_data.get('headers', [])
        rows = report_obj.report_data.get('rows', [])
        
        if headers and rows:
            # Convert dict rows to lists in the correct header order
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
        
        # Summary if available
        summary = report_obj.report_data.get('summary', [])
        if summary:
            elements.append(Paragraph(self.get_translated_text(report_obj, 'Summary'), subtitle_style))
            elements.append(Spacer(1, 12))
            
            # Get all unique keys from the summary
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
        
        # Footer info
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
        
        # Header
        header_text = "FICCT E-Commerce"
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawString(72, 800, header_text)
        
        # Footer with page number
        canvas.setFont('Helvetica', 9)
        page_text = f"{self.get_translated_text(None, 'Page')} {doc.page}"
        canvas.drawString(72, 30, page_text)
        
        canvas.restoreState()
        
    def generate_excel_content(self, report_obj):
        wb = Workbook()
        ws = wb.active
        ws.title = report_obj.report_type[:31]  # Excel sheet names must be <= 31 chars
        
        # Title
        ws['A1'] = report_obj.report_data.get('title', report_obj.name)
        ws.merge_cells('A1:E1')
        title_cell = ws['A1']
        title_cell.font = Font(size=16, bold=True)
        
        # Date range if available
        date_range = report_obj.report_data.get('date_range')
        if date_range:
            ws['A2'] = f"{self.get_translated_text(report_obj, 'Date Range')}: {date_range}"
            ws.merge_cells('A2:E2')
        
        # Report data
        headers = report_obj.report_data.get('headers', [])
        rows = report_obj.report_data.get('rows', [])
        
        # Starting row for headers
        row_idx = 4
        
        if headers and rows:
            # Add headers
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                
            # Add data rows
            for row_data in rows:
                row_idx += 1
                for col_idx, header in enumerate(headers, 1):
                    ws.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
        
        # Summary if available
        summary = report_obj.report_data.get('summary', [])
        if summary:
            row_idx += 2
            ws.cell(row=row_idx, column=1, value=self.get_translated_text(report_obj, 'Summary'))
            ws.cell(row=row_idx, column=1).font = Font(size=14, bold=True)
            row_idx += 1
            
            # Get all unique keys from the summary
            summary_headers = set()
            for item in summary:
                summary_headers.update(item.keys())
            summary_headers = list(summary_headers)
            
            # Add summary headers
            for col_idx, header in enumerate(summary_headers, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                
            # Add summary data
            for item in summary:
                row_idx += 1
                for col_idx, header in enumerate(summary_headers, 1):
                    ws.cell(row=row_idx, column=col_idx, value=item.get(header, ""))
        
        # Footer info
        row_idx += 2
        footer_text = f"{self.get_translated_text(report_obj, 'Report Date')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if report_obj.user:
            footer_text += f", {self.get_translated_text(report_obj, 'Generated by')}: {report_obj.user.first_name} {report_obj.user.last_name}"
        ws.cell(row=row_idx, column=1, value=footer_text)
        
        # Auto-adjust column widths
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