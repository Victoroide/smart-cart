from rest_framework import serializers
from core.models import LoggerService
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

class LoggerServiceSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField(read_only=True)
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_user_email(self, obj):
        return obj.user.email if obj.user else None
    
    class Meta:
        model = LoggerService
        fields = [
            'id', 
            'user', 
            'user_email',
            'action', 
            'table_name', 
            'description', 
            'level',
            'ip_address', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']