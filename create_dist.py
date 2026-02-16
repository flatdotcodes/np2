import os
import shutil
import zipfile
import glob
from datetime import datetime

DIST_DIR = 'dist'
RELEASE_NAME = 'np2_release'
IGNORE_PATTERNS = [
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git',
    '.gitignore',
    '.idea',
    '.vscode',
    'dist',
    'build',
    '*.egg-info',
    'venv',
    '.env',
    'tests', 
    'test_files',
    '.np2',
    'perf_log.txt',
    'create_dist.py' 
]

def create_distribution():
    print(f"Creating distribution in {DIST_DIR}...")
    
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)
    
    # Create a clean folder for the release
    release_path = os.path.join(DIST_DIR, RELEASE_NAME)
    
    print(f"Copying project files to {release_path}...")
    
    # Use shutil.copytree with ignore patterns
    shutil.copytree('.', release_path, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS, '.*'))
    
    # Create zip archive
    zip_name = f"{RELEASE_NAME}_{datetime.now().strftime('%Y%m%d')}"
    zip_path = os.path.join(DIST_DIR, zip_name)
    
    print(f"Zipping to {zip_path}.zip...")
    shutil.make_archive(zip_path, 'zip', DIST_DIR, RELEASE_NAME)
    
    print("Distribution created successfully!")
    print(f"Folder: {release_path}")
    print(f"Archive: {zip_path}.zip")

if __name__ == '__main__':
    create_distribution()
