from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime, timedelta
from io import BytesIO
import os
from django.conf import settings
from django.core.files.base import ContentFile
from uuid import uuid4

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from core.models import LoggerService
from core.pagination import CustomPagination

from .models import Report
from .serializers import ReportSerializer, ReportCreateSerializer
from app.orders.models import Order, OrderItem, Payment
from app.products.models import Product, Inventory

class ReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            if not request.user.is_staff:
                reports = Report.objects.filter(user=request.user).order_by('-created_at')
            else:
                reports = Report.objects.all().order_by('-created_at')
                
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(reports, request)
            
            serializer = ReportSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Report',
                description='Error on list reports: ' + str(e)
            )
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        with transaction.atomic():
            try:
                serializer = ReportCreateSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                report_obj = serializer.save(user=request.user if request.user.is_authenticated else None)
                
                data = None
                if report_obj.report_type == 'sales_by_customer':
                    data = self.generate_sales_by_customer_data(report_obj)
                elif report_obj.report_type == 'best_sellers':
                    data = self.generate_best_sellers_data(report_obj)
                elif report_obj.report_type == 'sales_by_period':
                    data = self.generate_sales_by_period_data(report_obj)
                elif report_obj.report_type == 'product_performance':
                    data = self.generate_product_performance_data(report_obj)
                elif report_obj.report_type == 'inventory_status':
                    data = self.generate_inventory_status_data(report_obj)
                else:
                    return Response({"detail": "Unknown report type"}, status=400)
                
                report_obj.report_data = data
                
                if report_obj.format == 'pdf':
                    file_content = self.generate_pdf_content(report_obj)
                    file_name = f"{report_obj.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    report_obj.file_path.save(file_name, ContentFile(file_content))
                elif report_obj.format == 'excel':
                    file_content = self.generate_excel_content(report_obj)
                    file_name = f"{report_obj.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    report_obj.file_path.save(file_name, ContentFile(file_content))
                
                report_obj.save()
                
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Report',
                    description=f'Created report {report_obj.id}'
                )
                
                return Response(ReportSerializer(report_obj).data)
                
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Report',
                    description='Error on create report: ' + str(e)
                )
                return Response({"error": str(e)}, status=500)

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
                'USD': 'USD',
                'BS': 'Bs'
            }
        }
        
        lang = report.language if report.language in translations else 'en'
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
            customer_name = order.user.email if order.user else 'Guest'
            if customer_name not in customer_totals:
                customer_totals[customer_name] = {'USD': 0, 'BS': 0}
                
            amount = float(order.total_amount)
            currency = order.currency
            customer_totals[customer_name][currency] += amount
            
            rows.append({
                headers[0]: order.id,
                headers[1]: customer_name,
                headers[2]: amount,
                headers[3]: currency,
                headers[4]: order.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        summary = []
        for customer, totals in sorted(customer_totals.items(), key=lambda x: sum(x[1].values()), reverse=True):
            for currency, amount in totals.items():
                if amount > 0:
                    summary.append({
                        headers[1]: customer,
                        headers[2]: amount,
                        headers[3]: currency
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
        
        items = OrderItem.objects.filter(order_id__in=order_ids).select_related('order')
        
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
            currency = item.order.currency
            
            if product_id not in product_stats:
                product_stats[product_id] = {
                    'name': item.product.name,
                    'quantity': 0,
                    'USD': 0,
                    'BS': 0
                }
            
            product_stats[product_id]['quantity'] += item.quantity
            revenue = float(item.unit_price * item.quantity)
            product_stats[product_id][currency] += revenue
            
        sorted_products = sorted(
            product_stats.items(), 
            key=lambda x: x[1]['quantity'], 
            reverse=True
        )
        
        rows = []
        for product_id, stats in sorted_products:
            if stats['USD'] > 0:
                rows.append({
                    headers[0]: product_id,
                    headers[1]: stats['name'],
                    headers[2]: stats['quantity'],
                    headers[3]: stats['USD'],
                    headers[4]: 'USD'
                })
            
            if stats['BS'] > 0:
                rows.append({
                    headers[0]: product_id,
                    headers[1]: stats['name'],
                    headers[2]: stats['quantity'],
                    headers[3]: stats['BS'],
                    headers[4]: 'BS'
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
            date_str = payment.created_at.strftime('%Y-%m-%d')
            currency = payment.order.currency
            
            if date_str not in daily_sales:
                daily_sales[date_str] = {
                    'USD': {'count': 0, 'total': 0},
                    'BS': {'count': 0, 'total': 0}
                }
            
            daily_sales[date_str][currency]['count'] += 1
            daily_sales[date_str][currency]['total'] += float(payment.amount)
            
        rows = []
        for date_str, currencies in sorted(daily_sales.items()):
            for currency, stats in currencies.items():
                if stats['count'] > 0:
                    rows.append({
                        headers[0]: date_str,
                        headers[1]: stats['count'],
                        headers[2]: stats['total'],
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
        
        items = OrderItem.objects.filter(order_id__in=order_ids).select_related('order', 'product')
        
        headers = [
            self.get_translated_text(report, 'Product Name'),
            self.get_translated_text(report, 'Quantity Sold'),
            self.get_translated_text(report, 'Revenue'),
            self.get_translated_text(report, 'Currency'),
            self.get_translated_text(report, 'Profit'),
            self.get_translated_text(report, 'Profit Margin')
        ]
        
        product_stats = {}
        for item in items:
            product_id = item.product.id
            product_name = item.product.name
            currency = item.order.currency
            
            key = f"{product_id}_{currency}"
            if key not in product_stats:
                product_stats[key] = {
                    'name': product_name,
                    'quantity': 0,
                    'revenue': 0,
                    'currency': currency,
                    'profit': 0,
                    'margin': 0
                }
                
            product_stats[key]['quantity'] += item.quantity
            revenue = float(item.unit_price * item.quantity)
            product_stats[key]['revenue'] += revenue
            
            cost = float(item.unit_price) * 0.7 * item.quantity
            profit = revenue - cost
            product_stats[key]['profit'] += profit
            
        for key, stats in product_stats.items():
            if stats['revenue'] > 0:
                stats['margin'] = (stats['profit'] / stats['revenue']) * 100
            
        sorted_products = sorted(
            product_stats.items(), 
            key=lambda x: x[1]['profit'], 
            reverse=True
        )
        
        rows = []
        for _, stats in sorted_products:
            rows.append({
                headers[0]: stats['name'],
                headers[1]: stats['quantity'],
                headers[2]: round(stats['revenue'], 2),
                headers[3]: stats['currency'],
                headers[4]: round(stats['profit'], 2),
                headers[5]: f"{round(stats['margin'], 1)}%"
            })
                
        return {
            'title': self.get_translated_text(report, 'Product Performance'),
            'date_range': f"{start_date} - {end_date}",
            'headers': headers,
            'rows': rows
        }
        
    def generate_inventory_status_data(self, report):
        headers = [
            self.get_translated_text(report, 'Product Name'),
            self.get_translated_text(report, 'Current Stock'),
            self.get_translated_text(report, 'Reorder Level'),
            self.get_translated_text(report, 'Status'),
            self.get_translated_text(report, 'Price USD'),
            self.get_translated_text(report, 'Price BS')
        ]
        
        inventory_items = Inventory.objects.all().select_related('product')
        
        rows = []
        for inv in inventory_items:
            if not inv.product.active:
                continue
                
            status = self.get_translated_text(report, 'In Stock')
            if inv.stock <= 0:
                status = self.get_translated_text(report, 'Out of Stock')
            elif inv.stock < inv.reorder_level:
                status = self.get_translated_text(report, 'Low Stock')
                
            rows.append({
                headers[0]: inv.product.name,
                headers[1]: inv.stock,
                headers[2]: inv.reorder_level,
                headers[3]: status,
                headers[4]: f"${float(inv.product.price_usd)}",
                headers[5]: f"Bs {float(inv.product.price_bs)}"
            })
                
        return {
            'title': self.get_translated_text(report, 'Inventory Status'),
            'date_range': datetime.now().strftime('%Y-%m-%d'),
            'headers': headers,
            'rows': rows
        }

    def generate_pdf_content(self, report_obj):
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=72, 
            leftMargin=72,
            topMargin=72, 
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        elements = []
        
        report_data = report_obj.report_data
        if not report_data:
            return None
        
        elements.append(Paragraph(report_data['title'], title_style))
        elements.append(Spacer(1, 12))
        
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        translator = lambda text: self.get_translated_text(report_obj, text)
        elements.append(Paragraph(f"{translator('Report Date')}: {report_date}", normal_style))
        elements.append(Paragraph(f"{translator('Date Range')}: {report_data['date_range']}", normal_style))
        elements.append(Paragraph(f"{translator('Generated by')}: {report_obj.user.email if report_obj.user else 'System'}", normal_style))
        elements.append(Spacer(1, 24))
        
        if 'rows' in report_data and report_data['rows']:
            headers = report_data['headers']
            data = [headers]
            
            for row in report_data['rows']:
                data_row = []
                for h in headers:
                    value = row.get(h, '')
                    if isinstance(value, float) and 'Amount' in h or 'Revenue' in h or 'Profit' in h:
                        currency = row.get('Currency', '')
                        if currency:
                            value = f"{value} {currency}"
                    data_row.append(value)
                data.append(data_row)
            
            table = Table(data, repeatRows=1)
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            table.setStyle(table_style)
            
            elements.append(table)
            elements.append(Spacer(1, 24))
            
        if 'summary' in report_data and report_data['summary']:
            elements.append(Paragraph(translator('Summary'), subtitle_style))
            elements.append(Spacer(1, 12))
            
            summary_data = []
            for item in report_data['summary']:
                row = []
                for key, value in item.items():
                    if isinstance(value, float) and ('Amount' in key or 'Revenue' in key):
                        currency = item.get('Currency', '')
                        if currency:
                            value = f"{value} {currency}"
                    row.append(value)
                summary_data.append(row)
                
            if summary_data:
                summary_table = Table(summary_data)
                
                summary_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ])
                summary_table.setStyle(summary_style)
                
                elements.append(summary_table)
        
        doc.build(
            elements, 
            onFirstPage=self._header_footer, 
            onLaterPages=self._header_footer
        )
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _header_footer(self, canvas, doc):
        canvas.saveState()
        
        page_num = canvas.getPageNumber()
        footer_text = f"Page {page_num}"
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(
            letter[0] - 72, 
            72/2, 
            footer_text
        )
        
        canvas.restoreState()
        
    def generate_excel_content(self, report_obj):
        report_data = report_obj.report_data
        if not report_data:
            return None
        
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Report"
        
        translator = lambda text: self.get_translated_text(report_obj, text)
        
        sheet['A1'] = report_data['title']
        sheet['A1'].font = Font(size=16, bold=True)
        sheet.merge_cells('A1:E1')
        
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        sheet['A3'] = f"{translator('Report Date')}:"
        sheet['B3'] = report_date
        sheet['A4'] = f"{translator('Date Range')}:"
        sheet['B4'] = report_data['date_range']
        sheet['A5'] = f"{translator('Generated by')}:"
        sheet['B5'] = report_obj.user.email if report_obj.user else 'System'
        
        for cell in [sheet['A3'], sheet['A4'], sheet['A5']]:
            cell.font = Font(bold=True)
        
        if 'rows' in report_data and report_data['rows']:
            row_num = 7
            
            headers = report_data['headers']
            for col_num, header in enumerate(headers, 1):
                cell = sheet.cell(row=row_num, column=col_num, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
                
                sheet.column_dimensions[get_column_letter(col_num)].width = max(15, len(str(header)) + 2)
            
            for row in report_data['rows']:
                row_num += 1
                for col_num, header in enumerate(headers, 1):
                    value = row.get(header, '')
                    
                    if isinstance(value, float) and ('Amount' in header or 'Revenue' in header or 'Profit' in header):
                        cell = sheet.cell(row=row_num, column=col_num, value=value)
                        cell.number_format = '#,##0.00'
                        
                        currency_col = None
                        for i, h in enumerate(headers, 1):
                            if h == 'Currency':
                                currency_col = i
                                break
                        
                        if currency_col:
                            sheet.cell(row=row_num, column=col_num).comment = openpyxl.comments.Comment(
                                f"Currency: {row.get('Currency', '')}", "Report System")
                    else:
                        sheet.cell(row=row_num, column=col_num, value=value)
            
            if 'summary' in report_data and report_data['summary']:
                row_num += 2
                sheet.cell(row=row_num, column=1, value=translator('Summary')).font = Font(bold=True)
                
                row_num += 1
                for item in report_data['summary']:
                    col_num = 1
                    for key, value in item.items():
                        if isinstance(value, float) and ('Amount' in key or 'Revenue' in key):
                            cell = sheet.cell(row=row_num, column=col_num, value=value)
                            cell.number_format = '#,##0.00'
                            
                            if 'Currency' in item:
                                cell.comment = openpyxl.comments.Comment(
                                    f"Currency: {item['Currency']}", "Report System")
                        else:
                            sheet.cell(row=row_num, column=col_num, value=value)
                        col_num += 1
                    row_num += 1
        
        excel_file = BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)
        
        return excel_file.getvalue()