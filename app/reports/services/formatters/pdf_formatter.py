import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.utils import timezone
from app.reports.constants.language_constants import RECEIPT_TRANSLATIONS

class PDFFormatter:
    def format_report(self, data, file_name, report_type, reports_dir):
        if report_type == 'order_receipt':
            return self._format_order_receipt(data, file_name)
        elif report_type == 'sales_by_customer':
            return self._format_sales_by_customer(data, file_name)
        elif report_type == 'best_sellers':
            return self._format_best_sellers(data, file_name)
        elif report_type == 'sales_by_period':
            return self._format_sales_by_period(data, file_name)
        elif report_type == 'product_performance':
            return self._format_product_performance(data, file_name)
        elif report_type == 'inventory_status':
            return self._format_inventory_status(data, file_name)
        elif report_type == 'customer_orders':
            return self._format_customer_orders(data, file_name)
        
        buffer = io.BytesIO()
        buffer.write(b"Error: Unknown report type")
        buffer.seek(0)
        return buffer, f"{file_name}.pdf"
    
    def _format_order_receipt(self, data, file_name):
        order = data.get('order')
        if not order:
            order = data
        
        language = data.get('language', 'en')
        texts = RECEIPT_TRANSLATIONS.get(language, RECEIPT_TRANSLATIONS['en'])
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, texts['title'])
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"{texts['order_number']}: {order.id}")
        c.drawString(50, height - 100, f"{texts['date']}: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
        c.drawString(50, height - 120, f"{texts['customer']}: {order.user.get_full_name() or order.user.email}")
        
        c.setStrokeColor(colors.black)
        c.line(50, height - 140, width - 50, height - 140)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 170, f"{texts['order_items']}:")
        
        table_data = [[texts['product'], texts['quantity'], texts['unit_price'], texts['total']]]
        
        y_position = height - 200
        total = 0
        
        for item in order.items.all():
            table_data.append([
                item.product.name if hasattr(item, 'product') and hasattr(item.product, 'name') else "Product",
                str(item.quantity),
                f"{item.unit_price} {order.currency}",
                f"{item.quantity * item.unit_price} {order.currency}"
            ])
            total += item.quantity * item.unit_price
            y_position -= 20
        
        table = Table(table_data, colWidths=[200, 50, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        table.wrapOn(c, width - 100, 500)
        table.drawOn(c, 50, y_position - (len(table_data) * 20))
        
        y_summary = y_position - (len(table_data) * 30)
        c.setFont("Helvetica", 12)
        c.drawString(300, y_summary, f"{texts['subtotal']}: {total} {order.currency}")
        
        if hasattr(order, 'discount_applied') and order.discount_applied:
            y_summary -= 20
            c.drawString(300, y_summary, f"{texts['discount']}: -{order.discount_applied} {order.currency}")
        
        if hasattr(order, 'payment') and order.payment:
            y_summary -= 20
            c.drawString(300, y_summary, f"{texts['payment_method']}: {order.payment.payment_method}")
            y_summary -= 20
            c.drawString(300, y_summary, f"{texts['payment_status']}: {order.payment.payment_status}")
        
        c.setFont("Helvetica-Bold", 14)
        y_summary -= 30
        c.drawString(300, y_summary, f"{texts['total']}: {order.total_amount} {order.currency}")
        
        c.setFont("Helvetica-Italic", 8)
        c.drawString(50, 30, texts['thank_you'])
        c.drawString(50, 15, f"{texts['receipt_generated']} {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        c.save()
        buffer.seek(0)
        file_path = f"{file_name}.pdf"
        return buffer, file_path
        
    def _format_sales_by_customer(self, data, file_name):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        sales_data = data.get('sales_data', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        language = data.get('language', 'en')
        
        elements = []
        
        title_style = styles['Heading1']
        title = Paragraph("Sales by Customer Report", title_style)
        elements.append(title)
        
        date_style = styles['Normal']
        date_text = f"Period: {start_date} to {end_date}"
        date_paragraph = Paragraph(date_text, date_style)
        elements.append(date_paragraph)
        
        elements.append(Spacer(1, 0.5*inch))
        
        table_data = [['Customer ID', 'Customer Name', 'Total Spent', 'Order Count', 'Average Order Value']]
        for customer in sales_data:
            table_data.append([
                str(customer.get('customer_id', '')),
                customer.get('customer_name', ''),
                f"${customer.get('total_spent', 0):.2f}",
                str(customer.get('order_count', 0)),
                f"${customer.get('average_order_value', 0):.2f}"
            ])
        
        table = Table(table_data, colWidths=[80, 150, 100, 80, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        pdf.build(elements)
        buffer.seek(0)
        
        file_path = f"{file_name}.pdf"
        return buffer, file_path
    
    def _format_best_sellers(self, data, file_name):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        products = data.get('products', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        elements = []
        
        title_style = styles['Heading1']
        title = Paragraph("Best Selling Products Report", title_style)
        elements.append(title)
        
        date_style = styles['Normal']
        date_text = f"Period: {start_date} to {end_date}"
        date_paragraph = Paragraph(date_text, date_style)
        elements.append(date_paragraph)
        
        elements.append(Spacer(1, 0.5*inch))
        
        table_data = [['Product ID', 'Product Name', 'Total Sold', 'Revenue']]
        for product in products:
            table_data.append([
                str(product.get('product_id', '')),
                product.get('product_name', ''),
                str(product.get('total_sold', 0)),
                f"${product.get('revenue', 0):.2f}"
            ])
        
        table = Table(table_data, colWidths=[80, 200, 100, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        pdf.build(elements)
        buffer.seek(0)
        
        file_path = f"{file_name}.pdf"
        return buffer, file_path
    
    def _format_sales_by_period(self, data, file_name):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        sales_data = data.get('sales_data', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        period = data.get('period', 'day')
        
        elements = []
        
        title_style = styles['Heading1']
        title = Paragraph(f"Sales by {period.capitalize()} Report", title_style)
        elements.append(title)
        
        date_style = styles['Normal']
        date_text = f"Period: {start_date} to {end_date}"
        date_paragraph = Paragraph(date_text, date_style)
        elements.append(date_paragraph)
        
        elements.append(Spacer(1, 0.5*inch))
        
        table_data = [['Date', 'Total Sales', 'Order Count']]
        for period_data in sales_data:
            table_data.append([
                str(period_data.get('period_date', '')),
                f"${period_data.get('total_sales', 0):.2f}",
                str(period_data.get('order_count', 0))
            ])
        
        table = Table(table_data, colWidths=[150, 150, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        pdf.build(elements)
        buffer.seek(0)
        
        file_path = f"{file_name}.pdf"
        return buffer, file_path
    
    def _format_product_performance(self, data, file_name):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30)
        styles = getSampleStyleSheet()
        
        performance_data = data.get('performance_data', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        elements = []
        
        title_style = styles['Heading1']
        title = Paragraph("Product Performance Report", title_style)
        elements.append(title)
        
        date_style = styles['Normal']
        date_text = f"Period: {start_date} to {end_date}"
        date_paragraph = Paragraph(date_text, date_style)
        elements.append(date_paragraph)
        
        elements.append(Spacer(1, 0.5*inch))
        
        table_data = [['Product ID', 'Product Name', 'Total Sold', 'Total Revenue', 'Avg Price']]
        for product in performance_data:
            table_data.append([
                str(product.get('product_id', '')),
                product.get('product_name', ''),
                str(product.get('total_sold', 0)),
                f"${product.get('total_revenue', 0):.2f}",
                f"${product.get('average_price', 0):.2f}"
            ])
        
        table = Table(table_data, colWidths=[60, 180, 80, 100, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        pdf.build(elements)
        buffer.seek(0)
        
        file_path = f"{file_name}.pdf"
        return buffer, file_path
    
    def _format_inventory_status(self, data, file_name):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30)
        styles = getSampleStyleSheet()
        
        inventory_data = data.get('inventory_data', [])
        date_generated = data.get('date_generated', timezone.now())
        
        elements = []
        
        title_style = styles['Heading1']
        title = Paragraph("Inventory Status Report", title_style)
        elements.append(title)
        
        date_style = styles['Normal']
        date_text = f"Generated on: {date_generated.strftime('%Y-%m-%d')}"
        date_paragraph = Paragraph(date_text, date_style)
        elements.append(date_paragraph)
        
        elements.append(Spacer(1, 0.5*inch))
        
        table_data = [['Product ID', 'Product Name', 'Stock', 'Price', 'Category', 'Status']]
        for product in inventory_data:
            table_data.append([
                str(product.get('product_id', '')),
                product.get('product_name', ''),
                str(product.get('stock', 0)),
                f"${product.get('price', 0):.2f}",
                product.get('category', ''),
                product.get('status', '')
            ])
        
        table = Table(table_data, colWidths=[60, 140, 50, 60, 100, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        pdf.build(elements)
        buffer.seek(0)
        
        file_path = f"{file_name}.pdf"
        return buffer, file_path
    
    def _format_customer_orders(self, data, file_name):
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        orders = data.get('orders', [])
        user = data.get('user', None)
        
        elements = []
        
        title_style = styles['Heading1']
        title = Paragraph("Customer Orders Report", title_style)
        elements.append(title)
        
        if user:
            customer_info = f"Customer: {user.get_full_name() or user.email}"
            customer_paragraph = Paragraph(customer_info, styles['Normal'])
            elements.append(customer_paragraph)
        
        elements.append(Spacer(1, 0.5*inch))
        
        table_data = [['Order ID', 'Date', 'Total', 'Status']]
        for order in orders:
            table_data.append([
                str(order.id),
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                f"${order.total_amount:.2f}",
                order.status
            ])
        
        table = Table(table_data, colWidths=[70, 150, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer = Paragraph(footer_text, styles['Italic'])
        elements.append(footer)
        
        pdf.build(elements)
        buffer.seek(0)
        
        file_path = f"{file_name}.pdf"
        return buffer, file_path