from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import *

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'loyalty', CustomerLoyaltyViewSet, basename='customer-loyalty')
router.register(r'deliveries/profiles', DeliveryProfileViewSet)
router.register(r'deliveries/assignments', DeliveryAssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomLoginView.as_view(), name='custom-login'),
]
