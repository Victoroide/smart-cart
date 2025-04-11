from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import LoggerService
from .serializers import LoggerServiceSerializer

class LoggerServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoggerService.objects.all()
    serializer_class = LoggerServiceSerializer
    permission_classes = [permissions.IsAdminUser]

    def list(self, request, *args, **kwargs):
        try:
            data = self.queryset.values()
            return Response(data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='LoggerService',
                description='Error on list logs: ' + str(e)
            )
            raise e

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return Response({
                'id': instance.id,
                'user': instance.user.id if instance.user else None,
                'action': instance.action,
                'table_name': instance.table_name,
                'description': instance.description,
                'level': instance.level,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at
            })
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='LoggerService',
                description='Error on retrieve log: ' + str(e)
            )
            raise e
