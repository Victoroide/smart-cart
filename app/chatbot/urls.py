from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.chatbot.viewsets.chatbot_session_viewset import ChatbotSessionViewSet
from app.chatbot.viewsets.chatbot_message_viewset import ChatbotMessageViewSet
from app.chatbot.viewsets.chat_interaction_viewset import ChatInteractionViewSet

router = DefaultRouter()
router.register(r'sessions', ChatbotSessionViewSet)
router.register(r'messages', ChatbotMessageViewSet)
router.register(r'interaction', ChatInteractionViewSet, basename='chat-interaction')

urlpatterns = [
    path('', include(router.urls)),
]