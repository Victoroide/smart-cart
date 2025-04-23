from django.db import models
from core.models import TimestampedModel
from app.chatbot.models.chatbot_session_model import ChatbotSession

class ChatbotMessage(TimestampedModel):
    session = models.ForeignKey(ChatbotSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=5)
    message = models.TextField()