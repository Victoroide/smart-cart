from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import LoggerServiceViewSet
from .viewsets.database_viewset import *


router = DefaultRouter()
router.register(r'logs', LoggerServiceViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
    path('database/backup-restore/', DatabaseBackupRestoreView.as_view(), name='database-backup-restore'),
    path('database/backup-download/<str:filename>/', DatabaseBackupDownloadView.as_view(), name='database-backup-download'),
    path('database/restore/', DatabaseRestoreView.as_view(), name='database-restore'),
]