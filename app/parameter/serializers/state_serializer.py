from rest_framework import serializers
from app.parameter.models.state_model import State

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name', 'code', 'country']

class StateWithCitiesSerializer(serializers.ModelSerializer):
    from app.parameter.serializers.city_serializer import CitySerializer
    cities = CitySerializer(many=True, read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = State
        fields = ['id', 'name', 'code', 'country', 'country_name', 'cities']