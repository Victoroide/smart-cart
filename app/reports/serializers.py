from rest_framework import serializers
from .models import Report
from drf_spectacular.utils import extend_schema_field, OpenApiExample

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'report_type', 'format',
            'start_date', 'end_date', 'language', 'report_data', 'file_path',
            'user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_data', 'file_path', 'user', 'created_at', 'updated_at']

class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'name', 'report_type', 'format',
            'start_date', 'end_date', 'language'
        ]
        
    def validate_report_type(self, value):
        allowed_types = ['sales_by_customer', 'best_sellers', 'sales_by_period', 
                        'product_performance', 'inventory_status', 'my_orders']
        if value not in allowed_types:
            raise serializers.ValidationError(f"Report type must be one of: {', '.join(allowed_types)}")
        return value
    
    def validate_format(self, value):
        allowed_formats = ['json', 'pdf', 'excel']
        if value not in allowed_formats:
            raise serializers.ValidationError(f"Format must be one of: {', '.join(allowed_formats)}")
        return value