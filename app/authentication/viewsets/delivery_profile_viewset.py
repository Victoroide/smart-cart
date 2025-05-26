from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from core.models import LoggerService
from core.pagination import CustomPagination
from app.authentication.models import DeliveryProfile, User
from app.authentication.serializers import DeliveryProfileSerializer, UserSerializer
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.authtoken.models import Token

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
    
    @extend_schema(
        description="Register as a new delivery person (mobile app registration)",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string', 'format': 'password'},
                    'first_name': {'type': 'string'},
                    'last_name': {'type': 'string'},
                    'phone': {'type': 'string'},
                    'identification_number': {'type': 'string'},
                    'vehicle_type': {'type': 'string'},
                    'license_plate': {'type': 'string'}
                },
                'required': ['email', 'password', 'first_name', 'last_name', 'identification_number']
            }
        },
        responses={
            201: {
                'description': 'Delivery account created successfully',
                'content': {
                    'application/json': {
                        'type': 'object',
                        'properties': {
                            'user': {'type': 'object'},
                            'profile': {'type': 'object'},
                            'token': {'type': 'string'}
                        }
                    }
                }
            },
            400: OpenApiResponse(description="Invalid data or email already exists")
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Register as a new delivery person through the mobile app.
        Creates both User and DeliveryProfile in a single request.
        """
        with transaction.atomic():
            try:
                user_data = {
                    'email': request.data.get('email'),
                    'password': request.data.get('password'),
                    'first_name': request.data.get('first_name'),
                    'last_name': request.data.get('last_name'),
                    'phone': request.data.get('phone'),
                    'role': 'delivery',
                }
                
                user_serializer = UserSerializer(data=user_data)
                if not user_serializer.is_valid():
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                if User.objects.filter(email=user_data['email']).exists():
                    return Response(
                        {"error": "This email address is already registered"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user = user_serializer.save()
                user.set_password(user_data['password'])
                user.save()
                
                profile_data = {
                    'user_id': user.id,
                    'identification_number': request.data.get('identification_number'),
                    'vehicle_type': request.data.get('vehicle_type'),
                    'license_plate': request.data.get('license_plate'),
                    'status': 'available'
                }
                
                profile_serializer = self.get_serializer(data=profile_data)
                if not profile_serializer.is_valid():
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                profile = profile_serializer.save()
                
                token, _ = Token.objects.get_or_create(user=user)
                
                LoggerService.objects.create(
                    user=user,
                    action='DELIVERY_REGISTRATION',
                    table_name='User, DeliveryProfile',
                    description=f'New delivery person registered: {user.email}'
                )
                
                return Response({
                    'user': UserSerializer(user).data,
                    'profile': self.get_serializer(profile).data,
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {"error": f"Error registering delivery account: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        if request.user.role != 'delivery':
            return Response({"detail": "Only delivery people can access this resource"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = DeliveryProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except DeliveryProfile.DoesNotExist:
            return Response({"detail": "Delivery profile not found"}, 
                           status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def set_available(self, request, pk=None):
        profile = self.get_object()
        profile.status = 'available'
        profile.save()
        
        LoggerService.objects.create(
            user=request.user,
            action='SET_AVAILABLE',
            table_name='DeliveryProfile',
            description=f'Delivery person {profile.user.id} marked as available'
        )
        
        return Response(self.get_serializer(profile).data)
    
    @action(detail=True, methods=['post'])
    def set_busy(self, request, pk=None):
        profile = self.get_object()
        profile.status = 'busy'
        profile.save()
        
        LoggerService.objects.create(
            user=request.user,
            action='SET_BUSY',
            table_name='DeliveryProfile',
            description=f'Delivery person {profile.user.id} marked as busy'
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
            description=f'Delivery person {profile.user.id} marked as offline'
        )
        
        return Response(self.get_serializer(profile).data)