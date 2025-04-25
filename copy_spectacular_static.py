import os
import shutil
import drf_spectacular_sidecar
from pathlib import Path

def extract_spectacular_static():
    try:
        print("Extracting Spectacular static files locally...")
        sidecar_path = Path(drf_spectacular_sidecar.__file__).parent
        swagger_ui_dist_source = sidecar_path / 'swagger-ui-dist'
        
        base_dir = Path(__file__).resolve().parent
        target_dir = base_dir / 'staticfiles' / 'drf_spectacular_sidecar' / 'swagger-ui-dist'
        
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"Copying Spectacular files to {target_dir}")
        for item in swagger_ui_dist_source.iterdir():
            if item.is_file():
                shutil.copy(item, target_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
        
        print("Successfully extracted Spectacular static files")
        return True
    except Exception as e:
        print(f"Error extracting Spectacular static files: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    extract_spectacular_static()