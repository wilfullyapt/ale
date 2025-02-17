#!/usr/bin/env python3
import sys
import shutil
from pathlib import Path
import argparse
from typing import Optional, Set

def find_ale_directory() -> Optional[Path]:
    """
    Find the .ale directory in the current working directory.
    Returns None if not found.
    """
    current_dir = Path.cwd()
    ale_dir = current_dir / '.ale'
    return ale_dir if ale_dir.is_dir() else None

def get_mirror_directory(ale_dir: Path) -> Optional[Path]:
    """
    Get the mirror directory in .ale that matches the parent directory name.
    Returns None if not found.
    """
    project_dir = ale_dir.parent
    project_name = project_dir.name
    mirror_dir = ale_dir / project_name

    return mirror_dir if mirror_dir.is_dir() else None

def collect_files(directory: Path) -> Set[Path]:
    """
    Collect all files in a directory recursively.
    Returns a set of paths relative to the given directory.
    """
    files = set()
    for path in directory.rglob('*'):
        if path.is_file():
            files.add(path.relative_to(directory))
    return files

def merge_directories(project_dir: Path, mirror_dir: Path, dry_run: bool = False) -> None:
    """
    Merge files from mirror directory into project directory.
    For files that exist in both:
        - If they differ, overwrite project file with mirror file
    For files only in mirror:
        - Copy them to project
    """
    mirror_files = collect_files(mirror_dir)
    project_files = collect_files(project_dir)

    # Process all mirror files
    for rel_path in mirror_files:
        mirror_file = mirror_dir / rel_path
        project_file = project_dir / rel_path

        if rel_path in project_files:
            # File exists in both - check if they differ
            if not project_file.exists() or not files_are_identical(mirror_file, project_file):
                if dry_run:
                    print(f"Would overwrite: {rel_path}")
                else:
                    project_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(mirror_file, project_file)
                    print(f"Overwrote: {rel_path}")
        else:
            # File only in mirror - copy it
            if dry_run:
                print(f"Would copy: {rel_path}")
            else:
                project_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(mirror_file, project_file)
                print(f"Copied: {rel_path}")

def files_are_identical(file1: Path, file2: Path) -> bool:
    """Compare two files to see if they are identical"""
    if not (file1.exists() and file2.exists()):
        return False
    
    if file1.stat().st_size != file2.stat().st_size:
        return False

    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        while True:
            chunk1 = f1.read(8192)
            chunk2 = f2.read(8192)
            if chunk1 != chunk2:
                return False
            if not chunk1:  # EOF
                return True

def main() -> int:
    parser = argparse.ArgumentParser(description='Merge files from .ale mirror directory')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    args = parser.parse_args()

    ale_dir = find_ale_directory()
    if not ale_dir:
        print("Error: No .ale directory found in current working directory", file=sys.stderr)
        return 1

    mirror_dir = get_mirror_directory(ale_dir)
    if not mirror_dir:
        print("Error: No mirror directory found in .ale matching project name", file=sys.stderr)
        return 1

    project_dir = ale_dir.parent
    try:
        merge_directories(project_dir, mirror_dir, args.dry_run)
        return 0
    except Exception as e:
        print(f"Error during merge: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())