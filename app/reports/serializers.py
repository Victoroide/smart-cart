from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Report
from app.authentication.models import User 

class ReportSerializer(serializers.ModelSerializer):
    file_path = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 
            'user', 
            'name', 
            'report_type', 
            'language', 
            'format', 
            'start_date', 
            'end_date', 
            'file_path', 
            'report_data', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'file_path', 'report_data', 'created_at', 'updated_at']
    
    def get_file_path(self, obj):
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None

class ReportCreateSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(required=False, write_only=True, help_text=_("Required if report_type is 'order_receipt'."))

    class Meta:
        model = Report
        fields = [
            'name', 
            'report_type', 
            'language', 
            'format', 
            'start_date', 
            'end_date',
            'order_id' 
        ]

    def validate(self, data):
        report_type = data.get('report_type')
        order_id = data.get('order_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if report_type == 'order_receipt' and not order_id:
            raise serializers.ValidationError(_("Order ID is required for 'order_receipt' report type."))
        
        optional_date_reports = ['inventory_status', 'order_receipt']
        
        if report_type not in optional_date_reports:
            if not start_date:
                raise serializers.ValidationError({ "start_date": _("Start date is required for this report type.")})
            if not end_date:
                raise serializers.ValidationError({ "end_date": _("End date is required for this report type.")})

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(_("Start date cannot be after end date."))
            
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        validated_data.pop('order_id', None) 
        
        report = Report.objects.create(user=user, **validated_data)
        return report