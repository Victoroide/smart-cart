from rest_framework import serializers
from app.chatbot.models import ChatbotMessage

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