#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import shutil
from typing import Dict, Any, List
import fnmatch
import yaml

def find_cleanup_config() -> Path:
    """Find cleanup.yaml in .ale directory"""
    current_dir = Path.cwd()
    config_file = current_dir / '.ale' / 'cleanup.yaml'
    if not config_file.is_file():
        # Use example config from tools directory
        config_file = Path(__file__).parent / 'cleanup-example.yaml'
    return config_file

def load_config() -> Dict[str, Any]:
    """Load cleanup configuration"""
    config_file = find_cleanup_config()
    if not config_file.is_file():
        print("Error: No cleanup.yaml found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading cleanup config: {e}", file=sys.stderr)
        sys.exit(1)

def find_matches(patterns: List[str], root_dir: Path = None) -> List[Path]:
    """Find files matching patterns"""
    if root_dir is None:
        root_dir = Path.cwd()

    matches = []
    for pattern in patterns:
        if pattern.startswith('/'):
            # Absolute path relative to project root
            pattern = pattern[1:]
            search_root = root_dir
        else:
            # Relative path from current directory
            search_root = Path.cwd()

        for path in search_root.rglob('*'):
            if path.is_file() and fnmatch.fnmatch(str(path.relative_to(search_root)), pattern):
                matches.append(path)
    return matches

def cleanup_paths(paths: List[Path], dry_run: bool = False) -> None:
    """Remove files and directories"""
    for path in paths:
        try:
            if dry_run:
                print(f"Would remove: {path}")
                continue

            if path.is_file():
                path.unlink()
                print(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
        except Exception as e:
            print(f"Error removing {path}: {e}", file=sys.stderr)

def main() -> int:
    parser = argparse.ArgumentParser(description='ALE Cleanup Tool')
    parser.add_argument('group', nargs='?',
                       help='Cleanup group to run (e.g., "python", "node")')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be removed without actually removing')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List available cleanup groups')

    args = parser.parse_args()
    config = load_config()

    if args.list:
        print("\nAvailable cleanup groups:")
        for group, details in config.items():
            desc = details.get('description', 'No description')
            print(f"  {group}: {desc}")
        return 0

    if not args.group:
        parser.print_help()
        return 1

    if args.group not in config:
        print(f"Error: Cleanup group '{args.group}' not found", file=sys.stderr)
        print("\nAvailable groups:")
        for group in config:
            print(f"  {group}")
        return 1

    group_config = config[args.group]
    patterns = group_config.get('patterns', [])
    if not patterns:
        print(f"No patterns defined for group '{args.group}'", file=sys.stderr)
        return 1

    matches = find_matches(patterns)
    if not matches:
        print(f"No files found matching patterns in group '{args.group}'")
        return 0

    cleanup_paths(matches, args.dry_run)
    return 0

if __name__ == '__main__':
    sys.exit(main())