import os
import shutil
import boto3
from pathlib import Path
from decouple import config
from django.conf import settings

def copy_spectacular_static():
    try:
        import drf_spectacular_sidecar
        sidecar_path = Path(drf_spectacular_sidecar.__file__).parent
        swagger_ui_dist_source = sidecar_path / 'swagger-ui-dist'
        
        base_dir = Path(__file__).resolve().parent
        target_dir = base_dir / 'staticfiles' / 'drf_spectacular_sidecar' / 'swagger-ui-dist'
        
        if not target_dir.exists():
            os.makedirs(target_dir, exist_ok=True)
        
        for item in swagger_ui_dist_source.iterdir():
            if item.is_file():
                shutil.copy(item, target_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
        
        if settings.USE_S3:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            for root, _, files in os.walk(target_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, start=base_dir/'staticfiles')
                    s3_key = f'public/static/{relative_path}'
                    
                    s3_client.upload_file(
                        file_path, 
                        settings.AWS_STORAGE_BUCKET_NAME, 
                        s3_key,
                        ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/javascript'}
                    )
            
            print(f"Successfully uploaded Django Spectacular files to S3 bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
        
        return True
    except Exception as e:
        print(f"Error in copy_spectacular_static: {e}")
        return False

if __name__ == "__main__":
    copy_spectacular_static()