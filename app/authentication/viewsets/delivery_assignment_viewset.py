from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import LoggerService
from core.pagination import CustomPagination
from app.authentication.models import DeliveryAssignment, DeliveryProfile
from app.authentication.serializers import DeliveryAssignmentSerializer
from app.authentication.permissions import DeliveryAssignmentPermission
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from datetime import datetime

@extend_schema(tags=['DeliveryAssignment'])
class DeliveryAssignmentViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAssignment.objects.all()
    serializer_class = DeliveryAssignmentSerializer
    permission_classes = [DeliveryAssignmentPermission]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        queryset = DeliveryAssignment.objects.all()
        
        if not self.request.user.is_staff:
            if self.request.user.role == 'delivery':
                queryset = queryset.filter(delivery_person=self.request.user)
            elif self.request.user.role == 'customer':
                queryset = queryset.filter(delivery__order__user=self.request.user)
            
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset.order_by('-assignment_date')
    
    @extend_schema(
        description="Get current assignments for the logged-in delivery person",
        responses={
            200: DeliveryAssignmentSerializer(many=True),
            403: OpenApiResponse(description="User is not a delivery person")
        }
    )
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        if request.user.role != 'delivery':
            return Response({"detail": "Solo los repartidores pueden acceder a este recurso"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        queryset = DeliveryAssignment.objects.filter(
            delivery_person=request.user
        ).exclude(status='completed')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Mark an assignment as in progress (delivery started)",
        request=None,
        responses={
            200: DeliveryAssignmentSerializer,
            400: OpenApiResponse(description="Assignment is not in 'assigned' status"),
            404: OpenApiResponse(description="Assignment not found")
        }
    )
    @action(detail=True, methods=['post'])
    def start_delivery(self, request, pk=None):
        with transaction.atomic():
            try:
                assignment = self.get_object()
                
                if assignment.status != 'assigned':
                    return Response(
                        {"detail": "Solo se pueden iniciar entregas con estado 'asignado'"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                assignment.status = 'in_progress'
                assignment.start_date = datetime.now()
                assignment.save()
                
                if hasattr(assignment, 'delivery'):
                    delivery = assignment.delivery
                    delivery.delivery_status = 'in_progress'
                    delivery.save()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='START_DELIVERY',
                    table_name='DeliveryAssignment',
                    description=f'Entrega #{assignment.id} iniciada por repartidor {request.user.id}'
                )
                
                return Response(self.get_serializer(assignment).data)
            except DeliveryAssignment.DoesNotExist:
                return Response(
                    {"detail": "Asignación de entrega no encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )
    
    @extend_schema(
        description="Mark an assignment as completed",
        request=None,
        responses={
            200: DeliveryAssignmentSerializer,
            400: OpenApiResponse(description="Assignment is not in 'in_progress' status"),
            404: OpenApiResponse(description="Assignment not found")
        }
    )
    @action(detail=True, methods=['post'])
    def complete_delivery(self, request, pk=None):
        with transaction.atomic():
            try:
                assignment = self.get_object()
                
                if assignment.status != 'in_progress':
                    return Response(
                        {"detail": "Solo se pueden completar entregas con estado 'en progreso'"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                assignment.status = 'completed'
                assignment.completion_date = datetime.now()
                assignment.save()
                
                if assignment.delivery_person and hasattr(assignment.delivery_person, 'delivery_profile'):
                    profile = assignment.delivery_person.delivery_profile
                    profile.status = 'available'
                    profile.save()
                
                if hasattr(assignment, 'delivery'):
                    delivery = assignment.delivery
                    delivery.delivery_status = 'completed'
                    delivery.actual_delivery_date = datetime.now().date()
                    delivery.save()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='COMPLETE_DELIVERY',
                    table_name='DeliveryAssignment',
                    description=f'Entrega #{assignment.id} completada por repartidor {request.user.id}'
                )
                
                return Response(self.get_serializer(assignment).data)
            except DeliveryAssignment.DoesNotExist:
                return Response(
                    {"detail": "Asignación de entrega no encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )