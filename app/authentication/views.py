from rest_framework import viewsets, status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import LoggerService
from core.pagination import CustomPagination
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import *

User = get_user_model()

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        return obj.id == request.user.id

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(active=True)
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action in ['list', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        return super().retrieve(request, *args, **kwargs)

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_object_permissions(self):
        return [IsAdminOrOwner()]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                response = super().create(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='User',
                    description='Created user ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='User',
                    description='Error on create user: ' + str(e)
                )
                raise e

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                obj = self.get_object()
                perm = IsAdminOrOwner()
                if not perm.has_object_permission(request, self, obj):
                    return Response(status=status.HTTP_403_FORBIDDEN)
                response = super().update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='UPDATE',
                    table_name='User',
                    description='Updated user ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='User',
                    description='Error on update user: ' + str(e)
                )
                raise e

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            try:
                obj = self.get_object()
                perm = IsAdminOrOwner()
                if not perm.has_object_permission(request, self, obj):
                    return Response(status=status.HTTP_403_FORBIDDEN)
                response = super().partial_update(request, *args, **kwargs)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='PATCH',
                    table_name='User',
                    description='Partially updated user ' + str(response.data.get('id'))
                )
                return response
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='User',
                    description='Error on partial_update user: ' + str(e)
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
                    table_name='User',
                    description='Soft-deleted user ' + str(instance.id)
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='User',
                    description='Error on delete user: ' + str(e)
                )
                raise e

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Current password'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password to set')
            },
            example={
                "old_password": "currentPassword123",
                "new_password": "newSecurePassword456"
            }
        ),
        operation_description="Change user password. Requires old password for verification."
    )       
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='change-password')
    def change_password(self, request):
        with transaction.atomic():
            try:
                user = request.user
                serializer = ChangePasswordSerializer(data=request.data)
                
                if serializer.is_valid():
                    if not user.check_password(serializer.validated_data['old_password']):
                        return Response({"error": "Old password is incorrect"}, status=status.HTTP_403_FORBIDDEN)
                    
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    
                    LoggerService.objects.create(
                        user=user,
                        action='PASSWORD_CHANGE',
                        table_name='User',
                        description=f'User {user.id} changed password'
                    )
                    
                    return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='User',
                    description=f'Error changing password: {str(e)}'
                )
                return Response({"error": "An error occurred while changing the password"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token
        
    def validate(self, attrs):
        data = super().validate(attrs)
        
        user = self.user
        data.update({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })
        
        return data

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
