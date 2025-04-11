from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id',
            'user',
            'name',
            'report_type',
            'start_date',
            'end_date',
            'file_path',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'user',
            'file_path',
            'created_at',
            'updated_at'
        ]
