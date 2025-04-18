from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomLoginView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomLoginView.as_view(), name='custom-login'),
]
