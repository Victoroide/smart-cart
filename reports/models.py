from django.db import models
from core.models import TimestampedModel
from authentication.models import User

class Report(TimestampedModel):
    REPORT_TYPES = (
        ('sales_by_customer', 'Sales by Customer'),
        ('best_sellers', 'Best Sellers'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    file_path = models.CharField(max_length=255, null=True, blank=True)
