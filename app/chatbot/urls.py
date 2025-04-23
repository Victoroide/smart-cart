from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.chatbot.viewsets import ChatbotSessionViewSet, ChatbotMessageViewSet

router = DefaultRouter()
router.register(r'sessions', ChatbotSessionViewSet, basename='chatbot-session')
router.register(r'messages', ChatbotMessageViewSet, basename='chatbot-message')

urlpatterns = [
    path('', include(router.urls)),
]