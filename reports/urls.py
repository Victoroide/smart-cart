from django.urls import path
from .views import (
    ReportListView,
    ReportCreateView,
    ReportPDFView,
    ReportExcelView
)

urlpatterns = [
    path('', ReportListView.as_view(), name='report-list'),
    path('create/', ReportCreateView.as_view(), name='report-create'),
    path('<int:report_id>/pdf/', ReportPDFView.as_view(), name='report-pdf'),
    path('<int:report_id>/excel/', ReportExcelView.as_view(), name='report-excel'),
]
