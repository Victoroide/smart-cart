from rest_framework import serializers
from app.authentication.models import DeliveryProfile
from app.authentication.serializers.user_serializer import UserSerializer

class DeliveryProfileSerializer(serializers.ModelSerializer):
    user_data = UserSerializer(source='user', read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DeliveryProfile
        fields = [
            'id', 'user_id', 'user_data', 'identification_number', 'status',
            'status_display', 'vehicle_type', 'license_plate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']