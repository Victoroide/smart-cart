from rest_framework_simplejwt.views import TokenObtainPairView
from app.authentication.serializers import CustomTokenObtainPairSerializer

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer