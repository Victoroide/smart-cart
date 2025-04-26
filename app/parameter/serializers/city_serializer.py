from rest_framework import serializers
from app.parameter.models.city_model import City

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'state']