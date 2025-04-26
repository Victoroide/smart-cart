from django.db import models
from core.models import TimestampedModel
from app.authentication.models import User
from base.storage import PublicMediaStorage
import os

def report_file_path(instance, filename):
    return os.path.join('reports', str(instance.user.id) if instance.user else 'anonymous', filename)

class Report(TimestampedModel):
    REPORT_TYPES = (
        ('sales_by_customer', 'Sales by Customer'),
        ('best_sellers', 'Best Sellers'),
        ('sales_by_period', 'Sales by Period'),
        ('product_performance', 'Product Performance'),
        ('inventory_status', 'Inventory Status'),
    )
    
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('es', 'Español'),
    )
    
    FORMAT_CHOICES = (
        ('json', 'JSON'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='json')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    file_path = models.FileField(storage=PublicMediaStorage(custom_path='reports'), null=True, blank=True)
    report_data = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"