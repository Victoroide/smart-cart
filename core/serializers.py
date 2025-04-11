from rest_framework import serializers
from .models import LoggerService

class LoggerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoggerService
        fields = [
            'id',
            'user',
            'action',
            'table_name',
            'description',
            'level',
            'created_at',
            'updated_at'
        ]
