from rest_framework import serializers
from core.models import LoggerService

class LoggerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoggerService
        fields = '__all__'