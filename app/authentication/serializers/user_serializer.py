from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from app.authentication.serializers.customer_loyalty_serializer import CustomerLoyaltySerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    loyalty = CustomerLoyaltySerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'active', 'password', 'is_staff', 'is_superuser', 'loyalty']
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
        validated_data = self._sync_role_and_permissions(validated_data)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        from app.authentication.models import CustomerLoyalty
        CustomerLoyalty.objects.create(user=user)
        
        return user
    
    def update(self, instance, validated_data):
        validated_data = self._sync_role_and_permissions(validated_data)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password is not None:
            instance.set_password(password)
        
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value