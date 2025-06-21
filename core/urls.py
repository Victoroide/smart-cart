from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import LoggerServiceViewSet
from .viewsets.database_viewset import *


router = DefaultRouter()
router.register(r'logs', LoggerServiceViewSet, basename='log')


