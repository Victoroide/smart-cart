from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'active', 'password', 'is_staff', 'is_superuser']
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def _sync_role_and_permissions(self, data):
        if 'role' in data:
            if data['role'] == 'admin':
                data['is_staff'] = True
                data['is_superuser'] = True
            else:
                data['is_staff'] = False
                data['is_superuser'] = False
        elif 'is_staff' in data or 'is_superuser' in data:
            if data.get('is_staff', False) and data.get('is_superuser', False):
                data['role'] = 'admin'
            else:
                data['role'] = 'customer'
        
        if 'active' in data:
            data['is_active'] = data['active']
        
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        validated_data = self._sync_role_and_permissions(validated_data)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data = self._sync_role_and_permissions(validated_data)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance