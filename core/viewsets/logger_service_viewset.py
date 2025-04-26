from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from ..models import LoggerService
from ..serializers import LoggerServiceSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from core.pagination import CustomPagination

@extend_schema(
    tags=['Logger Service'],
    description='API endpoints for system activity logs. Only available to admin users.'
)
class LoggerServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoggerService.objects.all()
    serializer_class = LoggerServiceSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @extend_schema(
        summary='List all logs',
        description='Retrieves a paginated list of all system activity logs. Supports filtering by user, action, table, and level.',
        responses={
            200: LoggerServiceSerializer(many=True),
            403: OpenApiResponse(description='Permission denied'),
            500: OpenApiResponse(description='Server error'),
        },
        parameters=[
            OpenApiParameter(
                name='page', 
                description='Page number for pagination',
                required=False, 
                type=int
            ),
            OpenApiParameter(
                name='page_size', 
                description='Number of items per page',
                required=False, 
                type=int
            ),
            OpenApiParameter(
                name='user', 
                description='Filter logs by user ID',
                required=False, 
                type=int
            ),
            OpenApiParameter(
                name='action', 
                description='Filter logs by action type (CREATE, UPDATE, DELETE, ERROR, LOGIN, etc)',
                required=False, 
                type=str
            ),
            OpenApiParameter(
                name='table_name', 
                description='Filter logs by table name',
                required=False, 
                type=str
            ),
            OpenApiParameter(
                name='level', 
                description='Filter logs by level (INFO, WARNING, ERROR)',
                required=False, 
                type=str
            ),
            OpenApiParameter(
                name='start_date', 
                description='Filter logs created on or after this date (YYYY-MM-DD)',
                required=False, 
                type=OpenApiTypes.DATE
            ),
            OpenApiParameter(
                name='end_date', 
                description='Filter logs created on or before this date (YYYY-MM-DD)',
                required=False, 
                type=OpenApiTypes.DATE
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            
            user_id = request.query_params.get('user')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
                
            action = request.query_params.get('action')
            if action:
                queryset = queryset.filter(action=action)
                
            table_name = request.query_params.get('table_name')
            if table_name:
                queryset = queryset.filter(table_name=table_name)
                
            level = request.query_params.get('level')
            if level:
                queryset = queryset.filter(level=level)
                
            start_date = request.query_params.get('start_date')
            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)
                
            end_date = request.query_params.get('end_date')
            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)
            
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='LoggerService',
                description=f'Error on list logs: {str(e)}',
                ip_address=self.get_client_ip(request)
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary='Retrieve specific log',
        description='Gets detailed information about a specific log entry by ID.',
        responses={
            200: LoggerServiceSerializer,
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Log not found'),
            500: OpenApiResponse(description='Server error'),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return Response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='LoggerService',
                description=f'Error on retrieve log: {str(e)}',
                ip_address=self.get_client_ip(request)
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @extend_schema(
        summary='Get log statistics',
        description='Retrieves statistics about system logs, including counts by action type, table, and level.',
        responses={
            200: OpenApiTypes.OBJECT,
            403: OpenApiResponse(description='Permission denied'),
            500: OpenApiResponse(description='Server error'),
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        try:
            total_count = LoggerService.objects.count()
            
            action_counts = LoggerService.objects.values('action').annotate(count=models.Count('id'))
            
            table_counts = LoggerService.objects.values('table_name').annotate(count=models.Count('id'))
            
            level_counts = LoggerService.objects.values('level').annotate(count=models.Count('id'))
            
            from django.utils import timezone
            recent_count = LoggerService.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            
            return Response({
                'total_logs': total_count,
                'recent_logs': recent_count,
                'by_action': action_counts,
                'by_table': table_counts,
                'by_level': level_counts,
            })
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='LoggerService',
                description=f'Error on log statistics: {str(e)}',
                ip_address=self.get_client_ip(request)
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)