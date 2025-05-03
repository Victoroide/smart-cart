from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ReportViewSet

router = DefaultRouter()
router.register('', ReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]