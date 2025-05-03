from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from app.reports.models import Report
from app.reports.serializers import ReportSerializer
from app.reports.services.report_service import ReportService
from app.reports.constants.report_constants import REPORT_TYPES, REPORT_FORMATS
from core.models import LoggerService
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Reports'])
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by('-created_at')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @extend_schema(
        summary="Generate order receipt",
        description="Creates a PDF receipt for a specific order"
    )
    @action(detail=False, methods=['post'], url_path='order_receipt')
    def generate_order_receipt(self, request):
        try:
            order_id = request.data.get('order_id')
            language = request.data.get('language', 'en')
            format_type = request.data.get('format', 'pdf')
            
            if not order_id:
                return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Order Receipt #{order_id}",
                    report_type=REPORT_TYPES['ORDER_RECEIPT'],
                    format=format_type,
                    language=language
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report(order_id=order_id)
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated {format_type} receipt for order {order_id}'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Report',
                description=f'Error generating receipt: {str(e)}'
            )
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Report',
                description=f'Error generating receipt: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate receipt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Generate sales by customer report",
        description="Creates a report of sales grouped by customer"
    )
    @action(detail=False, methods=['post'], url_path='sales_by_customer')
    def generate_sales_by_customer(self, request):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            format_type = request.data.get('format', 'pdf')
            language = request.data.get('language', 'en')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Sales by Customer Report",
                    report_type=REPORT_TYPES['SALES_BY_CUSTOMER'],
                    format=format_type,
                    language=language,
                    start_date=start_date,
                    end_date=end_date
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated sales by customer report'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f'Error generating sales by customer report: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Generate best sellers report",
        description="Creates a report of best selling products"
    )
    @action(detail=False, methods=['post'], url_path='best_sellers')
    def generate_best_sellers(self, request):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            format_type = request.data.get('format', 'pdf')
            language = request.data.get('language', 'en')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Best Sellers Report",
                    report_type=REPORT_TYPES['BEST_SELLERS'],
                    format=format_type,
                    language=language,
                    start_date=start_date,
                    end_date=end_date
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated best sellers report'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f'Error generating best sellers report: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @extend_schema(
        summary="Generate sales by period report",
        description="Creates a report of sales grouped by time period"
    )
    @action(detail=False, methods=['post'], url_path='sales_by_period')
    def generate_sales_by_period(self, request):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            format_type = request.data.get('format', 'pdf')
            language = request.data.get('language', 'en')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            period = request.data.get('period', 'day')
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Sales by Period Report",
                    report_type=REPORT_TYPES['SALES_BY_PERIOD'],
                    format=format_type,
                    language=language,
                    start_date=start_date,
                    end_date=end_date,
                    report_data={'period': period}
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated sales by period report'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f'Error generating sales by period report: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Generate product performance report",
        description="Creates a performance report for products"
    )
    @action(detail=False, methods=['post'], url_path='product_performance')
    def generate_product_performance(self, request):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            format_type = request.data.get('format', 'pdf')
            language = request.data.get('language', 'en')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Product Performance Report",
                    report_type=REPORT_TYPES['PRODUCT_PERFORMANCE'],
                    format=format_type,
                    language=language,
                    start_date=start_date,
                    end_date=end_date
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated product performance report'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f'Error generating product performance report: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Generate inventory status report",
        description="Creates a report on current inventory status"
    )
    @action(detail=False, methods=['post'], url_path='inventory_status')
    def generate_inventory_status(self, request):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            format_type = request.data.get('format', 'pdf')
            language = request.data.get('language', 'en')
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Inventory Status Report",
                    report_type=REPORT_TYPES['INVENTORY_STATUS'],
                    format=format_type,
                    language=language
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated inventory status report'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f'Error generating inventory status report: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Generate customer orders report",
        description="Creates a report for a customer's orders"
    )
    @action(detail=False, methods=['post'], url_path='customer_orders')
    def generate_customer_orders(self, request):
        try:
            format_type = request.data.get('format', 'pdf')
            language = request.data.get('language', 'en')
            user_id = request.data.get('user_id')
            
            if request.user.is_staff and user_id:
                pass
            else:
                user_id = request.user.id
            
            with transaction.atomic():
                report = Report.objects.create(
                    user=request.user,
                    name=f"Customer Orders Report",
                    report_type=REPORT_TYPES['CUSTOMER_ORDERS'],
                    format=format_type,
                    language=language,
                    report_data={'user_id': user_id}
                )
                
                report_service = ReportService(report)
                file_url = report_service.generate_report()
                
                LoggerService.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Report',
                    description=f'Generated customer orders report for user {user_id}'
                )
                
            return Response({
                'id': report.id,
                'name': report.name,
                'file_url': file_url,
                'created_at': report.created_at,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            LoggerService.objects.create(
                user=request.user,
                action='ERROR',
                table_name='Report',
                description=f'Error generating customer orders report: {str(e)}'
            )
            return Response(
                {"error": f"Failed to generate report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )