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
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        if 'active' in validated_data:
            validated_data['is_active'] = validated_data['active']
        
        if validated_data.get('role') == 'admin':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        if 'active' in validated_data:
            validated_data['is_active'] = validated_data['active']
        
        if 'role' in validated_data:
            if validated_data['role'] == 'admin':
                validated_data['is_staff'] = True
                validated_data['is_superuser'] = True
            else:
                validated_data['is_staff'] = False
                validated_data['is_superuser'] = False
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance