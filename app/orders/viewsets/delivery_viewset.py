from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.orders.models import Delivery
from app.orders.serializers import DeliverySerializer
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from django.utils import timezone
from django.conf import settings

@extend_schema(tags=['Delivery'])
class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Delivery.objects.all()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(order__user=self.request.user)
            
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(delivery_status=status_param)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def delivered(self, request, pk=None):
        delivery = self.get_object()
        
        if delivery.delivery_status == 'delivered':
            return Response(
                {"detail": "Delivery is already marked as delivered."},
                status=status.HTTP_400_BAD_REQUEST
            )
                
        delivery.delivery_status = 'delivered'
        delivery.actual_delivery_date = timezone.now().date()
        delivery.save()
        
        return Response(
            self.get_serializer(delivery).data,
            status=status.HTTP_200_OK
        )

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Delivery',
                    description='Created delivery ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Delivery',
                    description='Error on create delivery: ' + str(e)
                )
                raise e
    
    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='Delivery',
                    description='Partially updated delivery ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Delivery',
                    description='Error on partial_update delivery: ' + str(e)
                )
                raise e
    
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                instance = self.get_object()
                instance.delete()
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='DELETE',
                    table_name='Delivery',
                    description='Deleted delivery ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Delivery',
                    description='Error on delete delivery: ' + str(e)
                )
                raise e