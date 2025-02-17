#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import subprocess
from datetime import datetime, timedelta

def count_files_by_type(root_dir: Path = None) -> Counter:
    """Count files by extension"""
    if root_dir is None:
        root_dir = Path.cwd()

    counter = Counter()
    for path in root_dir.rglob('*'):
        if path.is_file():
            ext = path.suffix.lower()
            if ext:
                counter[ext] += 1
            else:
                counter['(no extension)'] += 1
    return counter

def get_file_sizes(root_dir: Path = None) -> Dict[str, int]:
    """Get total size of files by extension"""
    if root_dir is None:
        root_dir = Path.cwd()

    sizes = defaultdict(int)
    for path in root_dir.rglob('*'):
        if path.is_file():
            ext = path.suffix.lower() or '(no extension)'
            sizes[ext] += path.stat().st_size
    return sizes

def format_size(size: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def get_git_stats() -> Dict[str, any]:
    """Get Git repository statistics"""
    try:
        # Check if git repo exists
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        return {}

    stats = {}
    
    # Get commit count
    result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'],
                          capture_output=True, text=True)
    stats['commits'] = int(result.stdout.strip()) if result.returncode == 0 else 0

    # Get contributor count
    result = subprocess.run(['git', 'shortlog', '-sn', '--all'],
                          capture_output=True, text=True)
    stats['contributors'] = len(result.stdout.splitlines()) if result.returncode == 0 else 0

    # Get active branches
    result = subprocess.run(['git', 'branch', '-r'],
                          capture_output=True, text=True)
    stats['branches'] = len(result.stdout.splitlines()) if result.returncode == 0 else 0

    # Get repository age
    result = subprocess.run(['git', 'log', '--reverse', '--format=%ct'],
                          capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        first_commit = datetime.fromtimestamp(int(result.stdout.splitlines()[0]))
        stats['age'] = (datetime.now() - first_commit).days

    return stats

def get_python_stats() -> Dict[str, any]:
    """Get Python-specific statistics"""
    stats = {}
    
    try:
        # Get test coverage if available
        result = subprocess.run(['coverage', 'report'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'TOTAL' in line:
                    stats['coverage'] = line.split()[-1].rstrip('%')
    except FileNotFoundError:
        pass

    try:
        # Get dependency count from poetry
        result = subprocess.run(['poetry', 'show', '--no-dev'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            stats['dependencies'] = len(result.stdout.splitlines())

        result = subprocess.run(['poetry', 'show', '--only', 'dev'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            stats['dev_dependencies'] = len(result.stdout.splitlines())
    except FileNotFoundError:
        pass

    return stats

def print_stats(root_dir: Path = None) -> None:
    """Print project statistics"""
    if root_dir is None:
        root_dir = Path.cwd()

    print("\n=== Project Statistics ===\n")

    # File counts and sizes
    counts = count_files_by_type(root_dir)
    sizes = get_file_sizes(root_dir)

    print("File Distribution:")
    total_files = sum(counts.values())
    total_size = sum(sizes.values())
    
    for ext, count in counts.most_common():
        size = sizes[ext]
        percentage = (count / total_files) * 100
        print(f"  {ext:12} {count:5d} files ({percentage:5.1f}%) - {format_size(size):>10}")

    print(f"\nTotal Files: {total_files}")
    print(f"Total Size:  {format_size(total_size)}")

    # Git statistics
    git_stats = get_git_stats()
    if git_stats:
        print("\nGit Statistics:")
        if 'commits' in git_stats:
            print(f"  Commits:      {git_stats['commits']}")
        if 'contributors' in git_stats:
            print(f"  Contributors: {git_stats['contributors']}")
        if 'branches' in git_stats:
            print(f"  Branches:     {git_stats['branches']}")
        if 'age' in git_stats:
            print(f"  Age:          {git_stats['age']} days")

    # Python statistics
    python_stats = get_python_stats()
    if python_stats:
        print("\nPython Statistics:")
        if 'coverage' in python_stats:
            print(f"  Test Coverage:      {python_stats['coverage']}%")
        if 'dependencies' in python_stats:
            print(f"  Dependencies:       {python_stats['dependencies']}")
        if 'dev_dependencies' in python_stats:
            print(f"  Dev Dependencies:   {python_stats['dev_dependencies']}")

def main() -> int:
    parser = argparse.ArgumentParser(description='ALE Project Statistics')
    parser.add_argument('--dir', '-d',
                       help='Directory to analyze (default: current directory)')

    args = parser.parse_args()
    root_dir = Path(args.dir) if args.dir else None

    try:
        print_stats(root_dir)
        return 0
    except Exception as e:
        print(f"Error gathering statistics: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())