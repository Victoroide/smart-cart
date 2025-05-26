from rest_framework import serializers
from app.authentication.models import DeliveryAssignment, User
from app.orders.serializers import DeliverySerializer
from app.authentication.serializers.user_serializer import UserSerializer

class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    delivery_data = DeliverySerializer(source='delivery', read_only=True)
    delivery_person_data = UserSerializer(source='delivery_person', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DeliveryAssignment
        fields = [
            'id', 'delivery', 'delivery_data', 'delivery_person', 'delivery_person_data', 
            'status', 'status_display', 'assignment_date', 'start_date', 
            'completion_date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'assignment_date', 'created_at', 'updated_at']