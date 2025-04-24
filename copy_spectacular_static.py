import os
import shutil
from pathlib import Path

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
        
        print("Successfully copied Django Spectacular static files to local directory")
        return True
    except Exception as e:
        print(f"Error copying Django Spectacular static files: {e}")
        return False

if __name__ == "__main__":
    copy_spectacular_static()