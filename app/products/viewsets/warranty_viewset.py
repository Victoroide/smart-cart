from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from core.models import LoggerService
from core.pagination import CustomPagination
from django.db import transaction
from app.products.models import Warranty
from app.products.serializers import WarrantySerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Warranty'])
class WarrantyViewSet(viewsets.ModelViewSet):
    queryset = Warranty.objects.filter(active=True)
    serializer_class = WarrantySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Warranty',
                    description='Created warranty ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Warranty',
                    description='Error on create warranty: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Warranty',
                    description='Partially updated warranty ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Warranty',
                    description='Error on partial_update warranty: ' + str(e)
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
                    table_name='Warranty',
                    description='Soft-deleted warranty ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Warranty',
                    description='Error on delete warranty: ' + str(e)
                )
                raise e