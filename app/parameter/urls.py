from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.parameter.viewsets import CountryViewSet, StateViewSet, CityViewSet

router = DefaultRouter()
router.register('countries', CountryViewSet, basename='country')
router.register('states', StateViewSet, basename='state')
router.register('cities', CityViewSet, basename='city')

urlpatterns = [
    path('', include(router.urls)),
]