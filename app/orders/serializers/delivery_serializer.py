from rest_framework import serializers
from app.orders.models import Delivery

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'id',
            'order',
            'delivery_address',
            'delivery_status',
            'tracking_info',
            'estimated_arrival',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']