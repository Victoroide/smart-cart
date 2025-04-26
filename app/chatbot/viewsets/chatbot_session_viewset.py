from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.chatbot.models import ChatbotSession
from app.chatbot.serializers import ChatbotSessionSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['ChatBotSession'])
class ChatbotSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatbotSession.objects.filter(active=True)
    serializer_class = ChatbotSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='ChatbotSession',
                    description='Created chatbot session ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='ChatbotSession',
                    description='Error on create chatbot session: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='ChatbotSession',
                    description='Partially updated chatbot session ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='ChatbotSession',
                    description='Error on partial_update chatbot session: ' + str(e)
                )
                raise e

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.active = False
                instance.save()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='ChatbotSession',
                    description='Soft-deleted chatbot session ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='ChatbotSession',
                    description='Error on delete chatbot session: ' + str(e)
                )
                raise e