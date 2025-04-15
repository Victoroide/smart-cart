from rest_framework import serializers
from .models import ChatbotSession, ChatbotMessage

class ChatbotSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotSession
        fields = [
            'id',
            'user',
            'session_token',
            'active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ChatbotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotMessage
        fields = [
            'id',
            'session',
            'sender',
            'message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
