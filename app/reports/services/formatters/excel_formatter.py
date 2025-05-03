import io
import xlsxwriter
from django.utils import timezone

class ExcelFormatter:
    def format_report(self, data, file_name, report_type, reports_dir):
        output = io.BytesIO()
        
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Add title format
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Add header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#CCCCCC',
            'border': 1,
            'align': 'center'
        })
        
        # Add date format
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        
        # Add currency format
        currency_format = workbook.add_format({'num_format': '$#,##0.00'})
        
        # Add cell format
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        if report_type == 'order_receipt':
            self._format_order_receipt(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        elif report_type == 'sales_by_customer':
            self._format_sales_by_customer(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        elif report_type == 'best_sellers':
            self._format_best_sellers(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        elif report_type == 'sales_by_period':
            self._format_sales_by_period(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        elif report_type == 'product_performance':
            self._format_product_performance(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        elif report_type == 'inventory_status':
            self._format_inventory_status(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        elif report_type == 'customer_orders':
            self._format_customer_orders(worksheet, data, title_format, header_format, date_format, currency_format, cell_format)
        
        workbook.close()
        
        output.seek(0)
        file_path = f"{file_name}.xlsx"
        
        return output, file_path
    
    def _format_order_receipt(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        order = data['order']
        language = data.get('language', 'en')
        
        # Title
        worksheet.write(0, 0, "ORDER RECEIPT", title_format)
        worksheet.write(1, 0, f"Order #: {order.id}")
        worksheet.write(2, 0, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
        worksheet.write(3, 0, f"Customer: {order.user.get_full_name() or order.user.email}")
        
        # Headers
        worksheet.write(5, 0, "Product", header_format)
        worksheet.write(5, 1, "Quantity", header_format)
        worksheet.write(5, 2, "Unit Price", header_format)
        worksheet.write(5, 3, "Total", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 40)  # Product
        worksheet.set_column(1, 1, 10)  # Quantity
        worksheet.set_column(2, 2, 15)  # Unit Price
        worksheet.set_column(3, 3, 15)  # Total
        
        # Items
        row = 6
        total = 0
        
        for item in order.items.all():
            worksheet.write(row, 0, item.product.name if hasattr(item, 'product') and hasattr(item.product, 'name') else "Product", cell_format)
            worksheet.write(row, 1, item.quantity, cell_format)
            worksheet.write_number(row, 2, item.unit_price, currency_format)
            worksheet.write_formula(row, 3, f"=B{row+1}*C{row+1}", currency_format)
            
            total += item.quantity * item.unit_price
            row += 1
        
        # Summary
        worksheet.write(row + 1, 2, "Subtotal:", cell_format)
        worksheet.write_number(row + 1, 3, total, currency_format)
        
        if hasattr(order, 'discount_applied') and order.discount_applied:
            worksheet.write(row + 2, 2, "Discount:", cell_format)
            worksheet.write_number(row + 2, 3, -order.discount_applied, currency_format)
            row += 1
        
        worksheet.write(row + 2, 2, "Total:", header_format)
        worksheet.write_number(row + 2, 3, order.total_amount, currency_format)
        
        if hasattr(order, 'payment') and order.payment:
            worksheet.write(row + 4, 0, f"Payment Method: {order.payment.payment_method}")
            worksheet.write(row + 5, 0, f"Payment Status: {order.payment.payment_status}")
        
        # Footer
        worksheet.write(row + 7, 0, "Thank you for your purchase!")
        worksheet.write(row + 8, 0, f"Receipt generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _format_sales_by_customer(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        sales_data = data.get('sales_data', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        # Title
        worksheet.write(0, 0, "SALES BY CUSTOMER REPORT", title_format)
        worksheet.write(1, 0, f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        worksheet.write(2, 0, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Headers
        worksheet.write(4, 0, "Customer ID", header_format)
        worksheet.write(4, 1, "Customer Name", header_format)
        worksheet.write(4, 2, "Total Spent", header_format)
        worksheet.write(4, 3, "Order Count", header_format)
        worksheet.write(4, 4, "Average Order Value", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 15)  # Customer ID
        worksheet.set_column(1, 1, 30)  # Customer Name
        worksheet.set_column(2, 2, 15)  # Total Spent
        worksheet.set_column(3, 3, 15)  # Order Count
        worksheet.set_column(4, 4, 20)  # Average Order Value
        
        # Data
        row = 5
        for customer in sales_data:
            worksheet.write(row, 0, customer.get('customer_id', ''), cell_format)
            worksheet.write(row, 1, customer.get('customer_name', ''), cell_format)
            worksheet.write_number(row, 2, customer.get('total_spent', 0), currency_format)
            worksheet.write(row, 3, customer.get('order_count', 0), cell_format)
            worksheet.write_number(row, 4, customer.get('average_order_value', 0), currency_format)
            row += 1
        
        # Summary
        if len(sales_data) > 0:
            total_spent = sum(customer.get('total_spent', 0) for customer in sales_data)
            total_orders = sum(customer.get('order_count', 0) for customer in sales_data)
            
            worksheet.write(row + 1, 1, "TOTALS:", header_format)
            worksheet.write_number(row + 1, 2, total_spent, currency_format)
            worksheet.write(row + 1, 3, total_orders, header_format)
            if total_orders > 0:
                worksheet.write_number(row + 1, 4, total_spent / total_orders, currency_format)
    
    def _format_best_sellers(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        products = data.get('products', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        # Title
        worksheet.write(0, 0, "BEST SELLERS REPORT", title_format)
        worksheet.write(1, 0, f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        worksheet.write(2, 0, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Headers
        worksheet.write(4, 0, "Product ID", header_format)
        worksheet.write(4, 1, "Product Name", header_format)
        worksheet.write(4, 2, "Total Sold", header_format)
        worksheet.write(4, 3, "Revenue", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 15)  # Product ID
        worksheet.set_column(1, 1, 40)  # Product Name
        worksheet.set_column(2, 2, 15)  # Total Sold
        worksheet.set_column(3, 3, 15)  # Revenue
        
        # Data
        row = 5
        for product in products:
            worksheet.write(row, 0, product.get('product_id', ''), cell_format)
            worksheet.write(row, 1, product.get('product_name', ''), cell_format)
            worksheet.write(row, 2, product.get('total_sold', 0), cell_format)
            worksheet.write_number(row, 3, product.get('revenue', 0), currency_format)
            row += 1
        
        # Summary
        if len(products) > 0:
            total_sold = sum(product.get('total_sold', 0) for product in products)
            total_revenue = sum(product.get('revenue', 0) for product in products)
            
            worksheet.write(row + 1, 1, "TOTALS:", header_format)
            worksheet.write(row + 1, 2, total_sold, header_format)
            worksheet.write_number(row + 1, 3, total_revenue, currency_format)
    
    def _format_sales_by_period(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        sales_data = data.get('sales_data', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        period = data.get('period', 'day')
        
        # Title
        worksheet.write(0, 0, f"SALES BY {period.upper()} REPORT", title_format)
        worksheet.write(1, 0, f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        worksheet.write(2, 0, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Headers
        worksheet.write(4, 0, "Date", header_format)
        worksheet.write(4, 1, "Total Sales", header_format)
        worksheet.write(4, 2, "Order Count", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 20)  # Date
        worksheet.set_column(1, 1, 15)  # Total Sales
        worksheet.set_column(2, 2, 15)  # Order Count
        
        # Data
        row = 5
        for period_data in sales_data:
            worksheet.write(row, 0, str(period_data.get('period_date', '')), cell_format)
            worksheet.write_number(row, 1, period_data.get('total_sales', 0), currency_format)
            worksheet.write(row, 2, period_data.get('order_count', 0), cell_format)
            row += 1
        
        # Summary
        if len(sales_data) > 0:
            total_sales = sum(period_data.get('total_sales', 0) for period_data in sales_data)
            total_orders = sum(period_data.get('order_count', 0) for period_data in sales_data)
            
            worksheet.write(row + 1, 0, "TOTALS:", header_format)
            worksheet.write_number(row + 1, 1, total_sales, currency_format)
            worksheet.write(row + 1, 2, total_orders, header_format)
    
    def _format_product_performance(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        performance_data = data.get('performance_data', [])
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        # Title
        worksheet.write(0, 0, "PRODUCT PERFORMANCE REPORT", title_format)
        worksheet.write(1, 0, f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        worksheet.write(2, 0, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Headers
        worksheet.write(4, 0, "Product ID", header_format)
        worksheet.write(4, 1, "Product Name", header_format)
        worksheet.write(4, 2, "Total Sold", header_format)
        worksheet.write(4, 3, "Total Revenue", header_format)
        worksheet.write(4, 4, "Average Price", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 15)  # Product ID
        worksheet.set_column(1, 1, 40)  # Product Name
        worksheet.set_column(2, 2, 15)  # Total Sold
        worksheet.set_column(3, 3, 15)  # Total Revenue
        worksheet.set_column(4, 4, 15)  # Average Price
        
        # Data
        row = 5
        for product in performance_data:
            worksheet.write(row, 0, product.get('product_id', ''), cell_format)
            worksheet.write(row, 1, product.get('product_name', ''), cell_format)
            worksheet.write(row, 2, product.get('total_sold', 0), cell_format)
            worksheet.write_number(row, 3, product.get('total_revenue', 0), currency_format)
            worksheet.write_number(row, 4, product.get('average_price', 0), currency_format)
            row += 1
        
        # Summary
        if len(performance_data) > 0:
            total_sold = sum(product.get('total_sold', 0) for product in performance_data)
            total_revenue = sum(product.get('total_revenue', 0) for product in performance_data)
            
            worksheet.write(row + 1, 1, "TOTALS:", header_format)
            worksheet.write(row + 1, 2, total_sold, header_format)
            worksheet.write_number(row + 1, 3, total_revenue, currency_format)
            if total_sold > 0:
                worksheet.write_number(row + 1, 4, total_revenue / total_sold, currency_format)
    
    def _format_inventory_status(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        inventory_data = data.get('inventory_data', [])
        date_generated = data.get('date_generated', timezone.now())
        
        # Title
        worksheet.write(0, 0, "INVENTORY STATUS REPORT", title_format)
        worksheet.write(1, 0, f"Generated: {date_generated.strftime('%Y-%m-%d %H:%M')}")
        
        # Headers
        worksheet.write(3, 0, "Product ID", header_format)
        worksheet.write(3, 1, "Product Name", header_format)
        worksheet.write(3, 2, "Stock", header_format)
        worksheet.write(3, 3, "Price", header_format)
        worksheet.write(3, 4, "Category", header_format)
        worksheet.write(3, 5, "Status", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 15)  # Product ID
        worksheet.set_column(1, 1, 40)  # Product Name
        worksheet.set_column(2, 2, 10)  # Stock
        worksheet.set_column(3, 3, 15)  # Price
        worksheet.set_column(4, 4, 20)  # Category
        worksheet.set_column(5, 5, 15)  # Status
        
        # Add status format
        low_stock_format = worksheet.book.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'color': 'red'
        })
        
        in_stock_format = worksheet.book.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'color': 'green'
        })
        
        # Data
        row = 4
        for product in inventory_data:
            status = product.get('status', '')
            status_format = low_stock_format if status == 'Low Stock' else in_stock_format
            
            worksheet.write(row, 0, product.get('product_id', ''), cell_format)
            worksheet.write(row, 1, product.get('product_name', ''), cell_format)
            worksheet.write(row, 2, product.get('stock', 0), cell_format)
            worksheet.write_number(row, 3, product.get('price', 0), currency_format)
            worksheet.write(row, 4, product.get('category', ''), cell_format)
            worksheet.write(row, 5, status, status_format)
            row += 1
        
        # Summary
        if len(inventory_data) > 0:
            total_products = len(inventory_data)
            total_stock = sum(product.get('stock', 0) for product in inventory_data)
            low_stock_count = sum(1 for product in inventory_data if product.get('status', '') == 'Low Stock')
            
            worksheet.write(row + 1, 0, "SUMMARY:", header_format)
            worksheet.write(row + 1, 1, "Total Products:")
            worksheet.write(row + 1, 2, total_products)
            worksheet.write(row + 2, 1, "Total Stock:")
            worksheet.write(row + 2, 2, total_stock)
            worksheet.write(row + 3, 1, "Low Stock Items:")
            worksheet.write(row + 3, 2, low_stock_count, low_stock_format if low_stock_count > 0 else cell_format)
    
    def _format_customer_orders(self, worksheet, data, title_format, header_format, date_format, currency_format, cell_format):
        orders = data.get('orders', [])
        user = data.get('user', None)
        
        # Title
        worksheet.write(0, 0, "CUSTOMER ORDERS REPORT", title_format)
        
        # Customer info
        if user:
            worksheet.write(1, 0, f"Customer: {user.get_full_name() or user.email}")
            worksheet.write(2, 0, f"Customer ID: {user.id}")
        worksheet.write(3, 0, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Headers
        worksheet.write(5, 0, "Order ID", header_format)
        worksheet.write(5, 1, "Date", header_format)
        worksheet.write(5, 2, "Total", header_format)
        worksheet.write(5, 3, "Status", header_format)
        
        # Set column widths
        worksheet.set_column(0, 0, 15)  # Order ID
        worksheet.set_column(1, 1, 20)  # Date
        worksheet.set_column(2, 2, 15)  # Total
        worksheet.set_column(3, 3, 20)  # Status
        
        # Data
        row = 6
        for order in orders:
            worksheet.write(row, 0, order.id, cell_format)
            worksheet.write(row, 1, order.created_at.strftime('%Y-%m-%d'), cell_format)
            worksheet.write_number(row, 2, order.total_amount, currency_format)
            worksheet.write(row, 3, order.status, cell_format)
            row += 1
        
        # Summary
        if len(orders) > 0:
            total_amount = sum(order.total_amount for order in orders)
            
            worksheet.write(row + 1, 1, "TOTAL:", header_format)
            worksheet.write_number(row + 1, 2, total_amount, currency_format)