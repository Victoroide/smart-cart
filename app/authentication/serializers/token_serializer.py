from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        token['email'] = user.email
        token['full_name'] = f"{user.first_name} {user.last_name}"
        token['role'] = user.role
        token['is_staff'] = user.is_staff
        
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