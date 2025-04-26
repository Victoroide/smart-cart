from rest_framework import serializers
from app.orders.models.delivery_address_model import DeliveryAddress
from app.parameter.serializers import CountrySerializer, StateSerializer, CitySerializer

class DeliveryAddressSerializer(serializers.ModelSerializer):
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = StateSerializer(source='state', read_only=True)
    city_data = CitySerializer(source='city', read_only=True)
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = DeliveryAddress
        fields = [
            'id', 'address_name', 'recipient_name', 'recipient_phone',
            'address_line1', 'address_line2', 'city', 'city_data',
            'state', 'state_data', 'country', 'country_data',
            'postal_code', 'is_default', 'full_address'
        ]
        read_only_fields = ['country_data', 'state_data', 'city_data', 'full_address']
        
    def validate(self, data):
        if 'city' in data and 'state' in data:
            if data['city'].state_id != data['state'].id:
                raise serializers.ValidationError({'city': 'City must belong to the selected state'})
                
        if 'state' in data and 'country' in data:
            if data['state'].country_id != data['country'].id:
                raise serializers.ValidationError({'state': 'State must belong to the selected country'})
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        if not DeliveryAddress.objects.filter(user=user).exists():
            validated_data['is_default'] = True
            
        return super().create(validated_data)