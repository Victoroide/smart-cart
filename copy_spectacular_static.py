import os
import shutil
import boto3
import drf_spectacular_sidecar
from pathlib import Path
from decouple import config
from django.conf import settings

def copy_spectacular_static():
    try:
        print("Starting copy of Spectacular static files...")
        # Source directory
        sidecar_path = Path(drf_spectacular_sidecar.__file__).parent
        swagger_ui_dist_source = sidecar_path / 'swagger-ui-dist'
        
        # Target directory
        base_dir = Path(__file__).resolve().parent
        target_dir = base_dir / 'staticfiles' / 'drf_spectacular_sidecar' / 'swagger-ui-dist'
        
        if not target_dir.exists():
            os.makedirs(target_dir, exist_ok=True)
            print(f"Created target directory: {target_dir}")
        
        # Copy files locally first
        print("Copying files locally...")
        for item in swagger_ui_dist_source.iterdir():
            if item.is_file():
                shutil.copy(item, target_dir / item.name)
                print(f"Copied file: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
                print(f"Copied directory: {item.name}")
        
        # Upload to S3
        if settings.USE_S3:
            print(f"Uploading to S3 bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            # Upload all files from the target directory to S3
            for root, _, files in os.walk(target_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, start=base_dir/'staticfiles')
                    s3_key = f'public/static/{relative_path}'
                    
                    # Determine content type based on file extension
                    content_type = 'application/octet-stream'  # default
                    if file.endswith('.js'):
                        content_type = 'application/javascript'
                    elif file.endswith('.css'):
                        content_type = 'text/css'
                    elif file.endswith('.html'):
                        content_type = 'text/html'
                    elif file.endswith('.png'):
                        content_type = 'image/png'
                    elif file.endswith('.svg'):
                        content_type = 'image/svg+xml'
                    
                    print(f"Uploading {file_path} to {s3_key} with type {content_type}")
                    # Upload the file with public-read ACL and correct content type
                    s3_client.upload_file(
                        file_path, 
                        settings.AWS_STORAGE_BUCKET_NAME, 
                        s3_key,
                        ExtraArgs={
                            'ACL': 'public-read', 
                            'ContentType': content_type
                        }
                    )
            
            print(f"Successfully uploaded Django Spectacular files to S3")
        
        return True
    except Exception as e:
        print(f"Error in copy_spectacular_static: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load Django settings
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
    django.setup()
    
    copy_spectacular_static()