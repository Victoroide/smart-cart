from rest_framework import serializers
from app.parameter.models.country_model import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code']

class CountryWithStatesSerializer(serializers.ModelSerializer):
    from app.parameter.serializers.state_serializer import StateSerializer
    states = StateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'states']