from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import LoggerService
from core.pagination import CustomPagination
from app.authentication.serializers import UserSerializer, ChangePasswordSerializer
from drf_spectacular.utils import extend_schema


User = get_user_model()

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.id == request.user.id

@extend_schema(tags=['User'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(active=True)
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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
                instance.is_active = False
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
            
    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        user = self.get_object()
        
        try:
            serializer = ChangePasswordSerializer(data=request.data)
            if serializer.is_valid():
                if not user.check_password(serializer.validated_data['old_password']):
                    return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
                
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