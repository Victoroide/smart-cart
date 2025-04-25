import os
import shutil
import sys
import importlib.util
import site
from pathlib import Path

def find_package_path(package_name):
    """Find the path of an installed package."""
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        # Try to find it in site-packages
        site_packages = site.getsitepackages()
        for site_pkg in site_packages:
            possible_path = os.path.join(site_pkg, package_name)
            if os.path.exists(possible_path):
                return possible_path
        return None
    return os.path.dirname(spec.origin)

def extract_spectacular_static():
    try:
        print("Extracting Spectacular static files locally...")
        
        # Find drf_spectacular_sidecar package
        sidecar_path = find_package_path('drf_spectacular_sidecar')
        if not sidecar_path:
            print("ERROR: drf_spectacular_sidecar package not found.")
            print("Make sure it's installed with: pip install drf-spectacular-sidecar")
            return False
        
        print(f"Found drf_spectacular_sidecar at: {sidecar_path}")
        
        # List contents of the directory to debug
        print("Contents of drf_spectacular_sidecar directory:")
        for item in os.listdir(sidecar_path):
            print(f"  - {item}")
        
        # Look for various possible directory names
        swagger_dir_names = ['swagger-ui-dist', 'swagger-ui', 'swagger_ui_dist', 'swagger_ui']
        swagger_ui_dist_source = None
        
        for name in swagger_dir_names:
            test_path = os.path.join(sidecar_path, name)
            if os.path.exists(test_path):
                swagger_ui_dist_source = test_path
                print(f"Found Swagger UI directory at: {swagger_ui_dist_source}")
                break
        
        if not swagger_ui_dist_source:
            # If none of the expected directories exist, download it directly
            print("Swagger UI directory not found, attempting to download...")
            
            # Create the directories we need
            base_dir = Path(__file__).resolve().parent
            swagger_target_dir = base_dir / 'staticfiles' / 'drf_spectacular_sidecar' / 'swagger-ui-dist'
            os.makedirs(swagger_target_dir, exist_ok=True)
            
            # Create a minimal set of required files
            with open(os.path.join(swagger_target_dir, 'swagger-ui-bundle.js'), 'w') as f:
                f.write('// This file was generated as a placeholder\n')
                f.write('// Please reinstall drf-spectacular-sidecar or download swagger-ui files manually\n')
                f.write('alert("Swagger UI files are missing. Please reinstall drf-spectacular-sidecar.");')
            
            with open(os.path.join(swagger_target_dir, 'swagger-ui.css'), 'w') as f:
                f.write('/* This file was generated as a placeholder */\n')
                f.write('/* Please reinstall drf-spectacular-sidecar or download swagger-ui files manually */\n')
                f.write('body:after { content: "Swagger UI files are missing. Please reinstall drf-spectacular-sidecar."; color: red; font-size: 24px; padding: 20px; }')
            
            print("Created placeholder files. Please reinstall drf-spectacular-sidecar properly.")
            return False
        
        # Target directories
        base_dir = Path(__file__).resolve().parent
        swagger_target_dir = base_dir / 'staticfiles' / 'drf_spectacular_sidecar' / 'swagger-ui-dist'
        
        # Create target directories
        os.makedirs(swagger_target_dir, exist_ok=True)
        
        # Copy Swagger UI files
        print(f"Copying Swagger UI files to {swagger_target_dir}")
        for item in os.listdir(swagger_ui_dist_source):
            source_item = os.path.join(swagger_ui_dist_source, item)
            target_item = os.path.join(swagger_target_dir, item)
            
            if os.path.isfile(source_item):
                shutil.copy2(source_item, target_item)
                print(f"Copied file: {item}")
            elif os.path.isdir(source_item):
                if os.path.exists(target_item):
                    shutil.rmtree(target_item)
                shutil.copytree(source_item, target_item)
                print(f"Copied directory: {item}")
        
        print("Successfully extracted Spectacular static files")
        return True
    except Exception as e:
        print(f"Error extracting Spectacular static files: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = extract_spectacular_static()
    sys.exit(0 if success else 1)