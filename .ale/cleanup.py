#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Clean up temporary and build files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    return parser.parse_args()

def cleanup(dry_run=False):
    patterns = [
        '*.pyc',
        '__pycache__',
        '*.pyo',
        '*.pyd',
        '.Python',
        'build/',
        'develop-eggs/',
        'dist/',
        'downloads/',
        'eggs/',
        '.eggs/',
        'lib/',
        'lib64/',
        'parts/',
        'sdist/',
        'var/',
        'wheels/',
        '*.egg-info/',
        '.installed.cfg',
        '*.egg',
        'MANIFEST',
        '.env',
        '.venv',
        'env/',
        'venv/',
        'ENV/',
        'env.bak/',
        'venv.bak/',
        '.coverage',
        '.coverage.*',
        '.cache',
        'nosetests.xml',
        'coverage.xml',
        '*.cover',
        '*.log',
        '.pytest_cache/',
        '.mypy_cache/',
        '.hypothesis/',
    ]

    cwd = Path.cwd()
    for pattern in patterns:
        for path in cwd.rglob(pattern):
            try:
                if dry_run:
                    print(f"Would remove: {path}")
                else:
                    if path.is_file():
                        path.unlink()
                        print(f"Removed file: {path}")
                    elif path.is_dir():
                        shutil.rmtree(path)
                        print(f"Removed directory: {path}")
            except Exception as e:
                print(f"Error removing {path}: {e}")

if __name__ == '__main__':
    args = parse_args()
    cleanup(args.dry_run)