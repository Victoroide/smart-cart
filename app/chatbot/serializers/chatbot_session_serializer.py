from rest_framework import serializers
from app.chatbot.models import ChatbotSession

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