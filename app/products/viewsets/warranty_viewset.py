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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        brand_id = request.query_params.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
            
        brand_name = request.query_params.get('brand_name')
        if brand_name:
            queryset = queryset.filter(brand__name__icontains=brand_name)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
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