from django.db import models
from django.utils import timezone
from core.models import TimestampedModel
from base.storage import PublicMediaStorage
from django.conf import settings

class Report(TimestampedModel):
    REPORT_TYPE_CHOICES = [
        ('sales_by_customer', 'Sales by Customer'),
        ('best_sellers', 'Best Sellers'),
        ('sales_by_period', 'Sales by Period'),
        ('product_performance', 'Product Performance'),
        ('inventory_status', 'Inventory Status'),
        ('order_receipt', 'Order Receipt'),
        ('customer_orders', 'Customer Orders'),
    ]
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Español'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='pdf')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    report_data = models.JSONField(null=True, blank=True)
    file_path = models.FileField(storage=PublicMediaStorage(), upload_to='reports', null=True, blank=True)