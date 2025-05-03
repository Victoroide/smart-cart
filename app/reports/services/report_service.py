import os
from datetime import datetime
from django.conf import settings

from app.reports.constants.report_constants import REPORT_TYPES, REPORT_FORMATS, USER_REPORT_PERMISSIONS
from app.reports.services.data_providers.admin_report_provider import AdminReportProvider
from app.reports.services.data_providers.customer_report_provider import CustomerReportProvider
from app.reports.services.formatters.pdf_formatter import PDFFormatter
from app.reports.services.formatters.excel_formatter import ExcelFormatter
from app.reports.services.formatters.json_formatter import JSONFormatter

class ReportService:
    def __init__(self, report):
        self.report = report
        self.user = report.user
        self.is_admin = self.user.is_staff
        self.report_type = report.report_type
        
        self.data_provider = None
        self.formatter = None
        self._setup_providers_and_formatters()
    
    def _setup_providers_and_formatters(self):
        if self.is_admin:
            self.data_provider = AdminReportProvider(self.user, self.report)
        else:
            self.data_provider = CustomerReportProvider(self.user, self.report)
        
        report_format = self.report.format.lower()
        if report_format == REPORT_FORMATS['PDF'].lower():
            self.formatter = PDFFormatter()
        elif report_format == REPORT_FORMATS['EXCEL'].lower():
            self.formatter = ExcelFormatter()
        elif report_format == REPORT_FORMATS['JSON'].lower():
            self.formatter = JSONFormatter()
        else:
            self.formatter = JSONFormatter()
    
    def generate_report(self, order_id=None):
        user_type = 'admin' if self.is_admin else 'customer'
        
        if self.report_type not in USER_REPORT_PERMISSIONS[user_type]:
            raise ValueError(f"User does not have permission to generate {self.report_type} reports")
        
        data = self._get_report_data(order_id)
        
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_name = f"{self.report_type}_{self.user.id}_{timestamp}"
        
        file_path = self.formatter.format_report(data, file_name, self.report_type, reports_dir)
        
        self.report.file_path = file_path
        self.report.report_data = data
        self.report.save()
        
        return file_path
    
    def _get_report_data(self, order_id=None):
        if self.report_type == REPORT_TYPES['SALES_BY_CUSTOMER']:
            return self.data_provider.get_sales_by_customer_data()
        elif self.report_type == REPORT_TYPES['BEST_SELLERS']:
            return self.data_provider.get_best_sellers_data()
        elif self.report_type == REPORT_TYPES['SALES_BY_PERIOD']:
            return self.data_provider.get_sales_by_period_data()
        elif self.report_type == REPORT_TYPES['PRODUCT_PERFORMANCE']:
            return self.data_provider.get_product_performance_data()
        elif self.report_type == REPORT_TYPES['INVENTORY_STATUS']:
            return self.data_provider.get_inventory_status_data()
        elif self.report_type == REPORT_TYPES['ORDER_RECEIPT']:
            return self.data_provider.get_order_receipt_data(order_id)
        elif self.report_type == REPORT_TYPES['CUSTOMER_ORDERS']:
            return self.data_provider.get_customer_orders_data()
        else:
            raise ValueError(f"Unknown report type: {self.report_type}")