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
            'language',
            'format',
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

class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['name', 'report_type', 'language', 'format', 'start_date', 'end_date']