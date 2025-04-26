from rest_framework import serializers
from app.orders.models import Delivery, Order
from app.parameter.serializers import CountrySerializer, StateSerializer, CitySerializer
from django.utils import timezone

class DeliverySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_delivery_status_display', read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(source='order', queryset=Order.objects.all())
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = StateSerializer(source='state', read_only=True)
    city_data = CitySerializer(source='city', read_only=True)
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = Delivery
        fields = [
            'order_id', 'recipient_name', 'recipient_phone',
            'address_line1', 'address_line2', 'city', 'city_data',
            'state', 'state_data', 'country', 'country_data',
            'postal_code', 'delivery_status', 'status_display',
            'estimated_arrival', 'actual_delivery_date', 
            'delivery_notes', 'full_address'
        ]
        read_only_fields = ['country_data', 'state_data', 'city_data', 
                          'status_display', 'actual_delivery_date', 'full_address']
    
    def validate(self, data):
        if 'delivery_status' in data and data['delivery_status'] == 'delivered' and not data.get('actual_delivery_date'):
            data['actual_delivery_date'] = timezone.now().date()
            
        if 'city' in data and 'state' in data:
            if data['city'].state_id != data['state'].id:
                raise serializers.ValidationError({'city': 'City must belong to the selected state'})
                
        if 'state' in data and 'country' in data:
            if data['state'].country_id != data['country'].id:
                raise serializers.ValidationError({'state': 'State must belong to the selected country'})
                
        return data

class DeliveryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'order', 'recipient_name', 'recipient_phone',
            'address_line1', 'address_line2', 'city',
            'state', 'country', 'postal_code',
            'estimated_arrival', 'delivery_notes'
        ]
    
    def validate(self, data):
        if 'city' in data and 'state' in data:
            if data['city'].state_id != data['state'].id:
                raise serializers.ValidationError({'city': 'City must belong to the selected state'})
                
        if 'state' in data and 'country' in data:
            if data['state'].country_id != data['country'].id:
                raise serializers.ValidationError({'state': 'State must belong to the selected country'})
                
        if hasattr(data.get('order'), 'delivery'):
            raise serializers.ValidationError({'order': 'This order already has a delivery record'})
            
        return data