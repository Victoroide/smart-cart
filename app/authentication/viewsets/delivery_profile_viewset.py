from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from core.models import LoggerService
from core.pagination import CustomPagination
from app.authentication.models import DeliveryProfile
from app.authentication.serializers import DeliveryProfileSerializer
from drf_spectacular.utils import extend_schema

class IsAdminOrSelfDelivery(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        return request.user.is_staff or request.user.role == 'delivery'
        
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        if request.user.role == 'delivery':
            return obj.user.id == request.user.id
            
        return False

@extend_schema(tags=['DeliveryProfile'])
class DeliveryProfileViewSet(viewsets.ModelViewSet):
    queryset = DeliveryProfile.objects.all()
    serializer_class = DeliveryProfileSerializer
    permission_classes = [IsAdminOrSelfDelivery]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        queryset = DeliveryProfile.objects.all()
        
        if not self.request.user.is_staff and self.request.user.role == 'delivery':
            queryset = queryset.filter(user=self.request.user)
            
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        if request.user.role != 'delivery':
            return Response({"detail": "Solo los repartidores pueden acceder a este recurso"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = DeliveryProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except DeliveryProfile.DoesNotExist:
            return Response({"detail": "Perfil de repartidor no encontrado"}, 
                           status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def set_available(self, request, pk=None):
        profile = self.get_object()
        profile.mark_as_available()
        
        LoggerService.objects.create(
            user=request.user,
            action='SET_AVAILABLE',
            table_name='DeliveryProfile',
            description=f'Repartidor {profile.user.id} marcado como disponible'
        )
        
        return Response(self.get_serializer(profile).data)
    
    @action(detail=True, methods=['post'])
    def set_busy(self, request, pk=None):
        profile = self.get_object()
        profile.assign_delivery()
        
        LoggerService.objects.create(
            user=request.user,
            action='SET_BUSY',
            table_name='DeliveryProfile',
            description=f'Repartidor {profile.user.id} marcado como ocupado'
        )
        
        return Response(self.get_serializer(profile).data)
    
    @action(detail=True, methods=['post'])
    def set_offline(self, request, pk=None):
        profile = self.get_object()
        profile.status = 'offline'
        profile.save()
        
        LoggerService.objects.create(
            user=request.user,
            action='SET_OFFLINE',
            table_name='DeliveryProfile',
            description=f'Repartidor {profile.user.id} marcado como fuera de línea'
        )
        
        return Response(self.get_serializer(profile).data)