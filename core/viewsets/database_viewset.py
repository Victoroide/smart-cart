import os
import uuid
import subprocess
import tempfile
import boto3
import platform
import shutil
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.models import LoggerService


class DatabaseBackupRestoreView(APIView):
    permission_classes = [IsAdminUser]
    backup_prefix = 'database_backups/'
    
    def _get_s3_client(self):
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
    
    def _get_db_settings(self):
        db_settings = settings.DATABASES['default']
        return {
            'name': db_settings['NAME'],
            'user': db_settings['USER'],
            'password': db_settings['PASSWORD'],
            'host': db_settings['HOST'],
            'port': db_settings['PORT'],
        }
    
    def _find_pg_binary(self, binary_name):
        pg_binary = shutil.which(binary_name)
        if pg_binary:
            return pg_binary

        if platform.system() == 'Windows':
            possible_paths = []
            for version in range(10, 21):
                possible_paths.append(f"C:\\Program Files\\PostgreSQL\\{version}\\bin\\{binary_name}.exe")
            for major in range(10, 21):
                for minor in range(0, 11):
                    possible_paths.append(f"C:\\Program Files\\PostgreSQL\\{major}.{minor}\\bin\\{binary_name}.exe")
            possible_paths.extend([
                f"C:\\Program Files\\PostgreSQL\\bin\\{binary_name}.exe",
                f"C:\\PostgreSQL\\bin\\{binary_name}.exe",
                f"C:\\Program Files (x86)\\PostgreSQL\\bin\\{binary_name}.exe",
                f"C:\\Program Files\\EnterpriseDB\\PostgreSQL\\bin\\{binary_name}.exe"
            ])
            for path in possible_paths:
                if os.path.isfile(path):
                    return path
            return None
        else:
            return None
    
    @extend_schema(
        tags=['Database'],
        summary="Create database backup",
        description="Creates a SQL backup file of the current database state in S3",
        responses={
            200: OpenApiExample(
                'Backup Created',
                value={
                    'detail': 'Database backup created successfully',
                    'filename': 'backup_20250517_123045.sql',
                    'download_url': '/api/core/database/backup-download/backup_20250517_123045.sql'
                },
                response_only=True,
            ),
            500: OpenApiExample(
                'Error',
                value={'error': 'Failed to create database backup'},
                response_only=True,
            ),
        }
    )
    def post(self, request):
        try:
            db_settings = self._get_db_settings()
            
            pg_dump_path = self._find_pg_binary('pg_dump')
            if not pg_dump_path:
                return Response(
                    {
                        'error': 'PostgreSQL pg_dump utility not found',
                        'details': 'Asegúrate de que pg_dump esté instalado y en el PATH del sistema en el servidor. Para Railway, revisa tu configuración de Nixpacks o Dockerfile para incluir las utilidades cliente de PostgreSQL.'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.sql"
            s3_path = f"{self.backup_prefix}{backup_filename}"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
                temp_path = temp_file.name
            
            try:
                env = os.environ.copy()
                if db_settings['password']:
                    env['PGPASSWORD'] = db_settings['password']
                
                connection_string = f"postgresql://{db_settings['user']}:{db_settings['password']}@{db_settings['host']}:{db_settings['port']}/{db_settings['name']}?sslmode=require"
                
                cmd = [
                    pg_dump_path,
                    '-d', connection_string,
                    '--format=plain',
                    '--no-owner',
                    '--no-acl',
                    '--file', temp_path
                ]
                
                process = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if process.returncode != 0:
                    raise Exception(f"pg_dump failed: {process.stderr}")
                
                s3_client = self._get_s3_client()
                with open(temp_path, 'rb') as f:
                    s3_client.upload_fileobj(
                        f, 
                        settings.AWS_STORAGE_BUCKET_NAME, 
                        s3_path
                    )
                
                LoggerService.objects.create(
                    user=request.user,
                    action='BACKUP',
                    table_name='Database',
                    description=f'Created database backup in S3: {backup_filename}'
                )
                
                download_url = f"/api/core/database/backup-download/{backup_filename}"
                return Response({
                    'detail': 'Database backup created successfully',
                    'filename': backup_filename,
                    'download_url': download_url
                })
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            try:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Database',
                    description=f'Backup error: {str(e)}'
                )
            except Exception:
                pass
                
            return Response(
                {'error': 'Failed to create database backup', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Database'],
        summary="List available backups",
        description="Returns a list of available database backup files in S3",
        responses={
            200: OpenApiExample(
                'Backup List',
                value={
                    'backups': [
                        {
                            'filename': 'backup_20250517_123045.sql',
                            'size_mb': 15.4,
                            'created_at': '2025-05-17T12:30:45',
                            'download_url': '/api/core/database/backup-download/backup_20250517_123045.sql'
                        }
                    ]
                },
                response_only=True,
            ),
            500: OpenApiExample(
                'Error',
                value={'error': 'Failed to retrieve backup list'},
                response_only=True,
            ),
        }
    )
    def get(self, request):
        try:
            s3_client = self._get_s3_client()
            
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix=self.backup_prefix
            )
            
            backups = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'] == self.backup_prefix:
                        continue
                    
                    filename = obj['Key'].replace(self.backup_prefix, '')
                    
                    if not filename or not filename.endswith('.sql'):
                        continue
                        
                    size_mb = round(obj['Size'] / (1024 * 1024), 2)
                    
                    backups.append({
                        'filename': filename,
                        'size_mb': size_mb,
                        'created_at': obj['LastModified'].isoformat(),
                        'download_url': f"/api/core/database/backup-download/{filename}"
                    })
            
            backups = sorted(backups, key=lambda x: x['created_at'], reverse=True)
            
            return Response({'backups': backups})
            
        except Exception as e:
            return Response(
                {'error': 'Failed to retrieve backup list from S3', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        tags=['Database'],
        summary="Delete backup file",
        description="Deletes a specific database backup from S3",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'filename': {
                        'type': 'string',
                        'description': 'Name of the backup file to delete'
                    }
                },
                'required': ['filename']
            }
        },
        responses={
            200: OpenApiExample(
                'Backup Deleted',
                value={'detail': 'Backup file deleted successfully'},
                response_only=True,
            ),
            400: OpenApiExample(
                'Bad Request',
                value={'error': 'No filename provided'},
                response_only=True,
            ),
            404: OpenApiExample(
                'Not Found',
                value={'error': 'Backup file not found'},
                response_only=True,
            ),
            500: OpenApiExample(
                'Error',
                value={'error': 'Failed to delete backup file'},
                response_only=True,
            ),
        }
    )
    def delete(self, request):
        try:
            data = request.data
            
            if 'filename' not in data:
                return Response(
                    {'error': 'No filename provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            filename = data['filename']
            s3_path = f"{self.backup_prefix}{filename}"
            
            s3_client = self._get_s3_client()
            try:
                s3_client.head_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=s3_path
                )
            except Exception:
                return Response(
                    {'error': 'Backup file not found in S3'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=s3_path
            )
            
            LoggerService.objects.create(
                user=request.user,
                action='DELETE',
                table_name='Database',
                description=f'Deleted database backup from S3: {filename}'
            )
            
            return Response({'detail': 'Backup file deleted successfully'})
            
        except Exception as e:
            try:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Database',
                    description=f'Delete backup error: {str(e)}'
                )
            except Exception:
                pass
                
            return Response(
                {'error': 'Failed to delete backup file', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatabaseBackupDownloadView(APIView):
    permission_classes = [IsAdminUser]
    backup_prefix = 'database_backups/'
    
    def _get_s3_client(self):
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
    
    @extend_schema(
        tags=['Database'],
        summary="Download backup file",
        description="Downloads a specific database backup SQL file from S3",
        parameters=[
            {
                'name': 'filename',
                'in': 'path',
                'required': True,
                'description': 'Name of the backup file to download',
                'schema': {'type': 'string'}
            }
        ],
        responses={
            200: OpenApiExample(
                'File Download',
                value="SQL file download",
                response_only=True,
            ),
            400: OpenApiExample(
                'Bad Request',
                value={'error': 'Filename parameter is required'},
                response_only=True,
            ),
            404: OpenApiExample(
                'Not Found',
                value={'error': 'Backup file not found'},
                response_only=True,
            ),
        }
    )
    def get(self, request, filename=None):
        try:
            if not filename:
                return Response(
                    {'error': 'Filename parameter is required', 'usage': '/api/core/database/backup-download/{filename}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            s3_path = f"{self.backup_prefix}{filename}"
            s3_client = self._get_s3_client()
            
            try:
                s3_client.head_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=s3_path
                )
            except Exception:
                return Response(
                    {'error': 'Backup file not found in S3'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                LoggerService.objects.create(
                    user=request.user,
                    action='DOWNLOAD',
                    table_name='Database',
                    description=f'Downloaded backup file from S3: {filename}'
                )
            except Exception:
                pass
                
            file_obj = s3_client.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=s3_path
            )
            file_content = file_obj['Body'].read()
            
            response = HttpResponse(file_content, content_type='application/sql')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            return Response(
                {'error': 'Failed to download backup file from S3', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatabaseRestoreView(APIView):
    permission_classes = [IsAdminUser]
    backup_prefix = 'database_backups/'
    
    def _get_s3_client(self):
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
    
    def _get_db_settings(self):
        db_settings = settings.DATABASES['default']
        return {
            'name': db_settings['NAME'],
            'user': db_settings['USER'],
            'password': db_settings['PASSWORD'],
            'host': db_settings['HOST'],
            'port': db_settings['PORT'],
        }
    
    def _find_pg_binary(self, binary_name):
        pg_binary = shutil.which(binary_name)
        if pg_binary:
            return pg_binary

        if platform.system() == 'Windows':
            possible_paths = []
            for version in range(10, 21):
                possible_paths.append(f"C:\\Program Files\\PostgreSQL\\{version}\\bin\\{binary_name}.exe")
            for major in range(10, 21):
                for minor in range(0, 11):
                    possible_paths.append(f"C:\\Program Files\\PostgreSQL\\{major}.{minor}\\bin\\{binary_name}.exe")
            possible_paths.extend([
                f"C:\\Program Files\\PostgreSQL\\bin\\{binary_name}.exe",
                f"C:\\PostgreSQL\\bin\\{binary_name}.exe",
                f"C:\\Program Files (x86)\\PostgreSQL\\bin\\{binary_name}.exe",
                f"C:\\Program Files\\EnterpriseDB\\PostgreSQL\\bin\\{binary_name}.exe"
            ])
            for path in possible_paths:
                if os.path.isfile(path):
                    return path
            return None
        else:
            return None
    
    @extend_schema(
        tags=['Database'],
        summary="Restore database from backup",
        description="Restores the database from an uploaded backup file",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'backup_file': {
                        'type': 'string', 
                        'format': 'binary',
                        'description': 'SQL backup file to restore from'
                    }
                },
                'required': ['backup_file']
            }
        },
        responses={
            200: OpenApiExample(
                'Restore Success',
                value={'detail': 'Database restored successfully'},
                response_only=True,
            ),
            400: OpenApiExample(
                'Bad Request',
                value={'error': 'No backup file provided'},
                response_only=True,
            ),
            500: OpenApiExample(
                'Error',
                value={'error': 'Failed to restore database'},
                response_only=True,
            ),
        }
    )
    def post(self, request):
        try:
            psql_path = self._find_pg_binary('psql')
            if not psql_path:
                return Response(
                    {
                        'error': 'PostgreSQL psql utility not found',
                        'details': 'Asegúrate de que psql esté instalado y en el PATH del sistema en el servidor. Para Railway, revisa tu configuración de Nixpacks o Dockerfile para incluir las utilidades cliente de PostgreSQL.'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if 'backup_file' not in request.FILES:
                return Response(
                    {'error': 'No backup file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            backup_file = request.FILES['backup_file']
            
            if not backup_file.name.endswith('.sql'):
                return Response(
                    {'error': 'Invalid backup file format. Must be a .sql file'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
                for chunk in backup_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            try:
                db_settings = self._get_db_settings()
                
                env = os.environ.copy()
                if db_settings['password']:
                    env['PGPASSWORD'] = db_settings['password']
                
                connection_string = f"postgresql://{db_settings['user']}:{db_settings['password']}@{db_settings['host']}:{db_settings['port']}/{db_settings['name']}?sslmode=require"
                
                cmd = [
                    psql_path,
                    '-d', connection_string,
                    '-f', temp_path,
                    '--single-transaction'
                ]
                
                process = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if process.returncode != 0:
                    raise Exception(f"psql restore failed: {process.stderr}")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                s3_filename = f"backup_{timestamp}.sql"
                s3_path = f"{self.backup_prefix}{s3_filename}"
                
                s3_client = self._get_s3_client()
                with open(temp_path, 'rb') as f:
                    s3_client.upload_fileobj(
                        f, 
                        settings.AWS_STORAGE_BUCKET_NAME, 
                        s3_path
                    )
                
                LoggerService.objects.create(
                    user=request.user,
                    action='RESTORE',
                    table_name='Database',
                    description=f'Restored database from uploaded file and saved to S3: {s3_filename}'
                )
                
                return Response({'detail': 'Database restored successfully'})
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            try:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Database',
                    description=f'Restore error: {str(e)}'
                )
            except Exception:
                pass
                
            return Response(
                {'error': 'Failed to restore database', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        tags=['Database'],
        summary="Restore from existing backup file",
        description="Restores database from an existing backup file in S3",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'filename': {
                        'type': 'string',
                        'description': 'Name of the backup file to restore from'
                    }
                },
                'required': ['filename']
            }
        },
        responses={
            200: OpenApiExample(
                'Restore Success',
                value={'detail': 'Database restored successfully from existing backup'},
                response_only=True,
            ),
            400: OpenApiExample(
                'Bad Request',
                value={'error': 'No filename provided'},
                response_only=True,
            ),
            404: OpenApiExample(
                'Not Found',
                value={'error': 'Backup file not found'},
                response_only=True,
            ),
            500: OpenApiExample(
                'Error',
                value={'error': 'Failed to restore database'},
                response_only=True,
            ),
        }
    )
    def put(self, request):
        try:
            psql_path = self._find_pg_binary('psql')
            if not psql_path:
                return Response(
                    {
                        'error': 'PostgreSQL psql utility not found',
                        'details': 'Asegúrate de que psql esté instalado y en el PATH del sistema en el servidor. Para Railway, revisa tu configuración de Nixpacks o Dockerfile para incluir las utilidades cliente de PostgreSQL.'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            data = request.data
            
            if 'filename' not in data:
                return Response(
                    {'error': 'No filename provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            filename = data['filename']
            s3_path = f"{self.backup_prefix}{filename}"
            
            s3_client = self._get_s3_client()
            try:
                s3_client.head_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=s3_path
                )
            except Exception:
                return Response(
                    {'error': 'Backup file not found in S3'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as temp_file:
                temp_path = temp_file.name
                
                s3_client.download_fileobj(
                    settings.AWS_STORAGE_BUCKET_NAME,
                    s3_path,
                    temp_file
                )
            
            try:
                db_settings = self._get_db_settings()
                
                env = os.environ.copy()
                if db_settings['password']:
                    env['PGPASSWORD'] = db_settings['password']
                
                connection_string = f"postgresql://{db_settings['user']}:{db_settings['password']}@{db_settings['host']}:{db_settings['port']}/{db_settings['name']}?sslmode=require"
                
                cmd = [
                    psql_path,
                    '-d', connection_string,
                    '-f', temp_path,
                    '--single-transaction'
                ]
                
                process = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if process.returncode != 0:
                    raise Exception(f"psql restore failed: {process.stderr}")
                
                LoggerService.objects.create(
                    user=request.user,
                    action='RESTORE',
                    table_name='Database',
                    description=f'Restored database from S3 backup: {filename}'
                )
                
                return Response({'detail': 'Database restored successfully from existing S3 backup'})
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            try:
                LoggerService.objects.create(
                    user=request.user,
                    action='ERROR',
                    table_name='Database',
                    description=f'Restore error: {str(e)}'
                )
            except Exception:
                pass
                
            return Response(
                {'error': 'Failed to restore database', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )