import os
import shutil
import sys
import requests
from pathlib import Path

def extract_spectacular_static():
    try:
        print("Extracting Spectacular static files directly...")
        
        base_dir = Path(__file__).resolve().parent
        target_dir = base_dir / 'staticfiles' / 'drf_spectacular_sidecar' / 'swagger-ui-dist'
        os.makedirs(target_dir, exist_ok=True)
        
        files_to_download = {
            'swagger-ui.css': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css',
            'swagger-ui-bundle.js': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js',
            'swagger-ui-standalone-preset.js': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js',
            'favicon-32x32.png': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/favicon-32x32.png'
        }
        
        for filename, url in files_to_download.items():
            print(f"Downloading {filename}...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(os.path.join(target_dir, filename), 'wb') as f:
                    f.write(response.content)
                print(f"Successfully downloaded {filename}")
            else:
                print(f"Failed to download {filename}: HTTP {response.status_code}")
        
        print("Files downloaded successfully")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        import subprocess
        print("Installing requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        
    success = extract_spectacular_static()
    sys.exit(0 if success else 1)