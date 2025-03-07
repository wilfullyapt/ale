#!/usr/bin/env python3
"""
Project statistics tool for analyzing project structure and metrics.

This tool provides insights into your project by analyzing various
aspects such as file distribution, Git statistics, and language-specific
metrics.

Features:
- File type distribution and sizes
- Git repository statistics (commits, contributors, age)
- Python-specific metrics (coverage, dependencies)
- Human-readable size formatting
- Directory-specific analysis
"""
import sys
import ast
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, NamedTuple
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

class CodeMetrics(NamedTuple):
    classes: int
    functions: int
    try_statements: int
    if_statements: int
    total_lines: int
    blank_lines: int
    comment_lines: int

def analyze_python_file(file_path: Path) -> CodeMetrics:
    """Analyze a Python file for various metrics"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()
        
    # Count blank lines and comment lines
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    total_lines = len(lines)
    
    # Parse AST for other metrics
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return CodeMetrics(0, 0, 0, 0, total_lines, blank_lines, comment_lines)
    
    class CodeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.classes = 0
            self.functions = 0
            self.try_statements = 0
            self.if_statements = 0
            
        def visit_ClassDef(self, node):
            self.classes += 1
            self.generic_visit(node)
            
        def visit_FunctionDef(self, node):
            self.functions += 1
            self.generic_visit(node)
            
        def visit_AsyncFunctionDef(self, node):
            self.functions += 1
            self.generic_visit(node)
            
        def visit_Try(self, node):
            self.try_statements += 1
            self.generic_visit(node)
            
        def visit_If(self, node):
            self.if_statements += 1
            self.generic_visit(node)
    
    visitor = CodeVisitor()
    visitor.visit(tree)
    
    return CodeMetrics(
        visitor.classes,
        visitor.functions,
        visitor.try_statements,
        visitor.if_statements,
        total_lines,
        blank_lines,
        comment_lines
    )

def get_python_stats() -> Dict[str, any]:
    """Get Python-specific statistics"""
    stats = {}
    
    # Analyze Python files in the project
    total_metrics = CodeMetrics(0, 0, 0, 0, 0, 0, 0)
    python_files = list(Path('.').rglob('*.py'))
    
    if python_files:
        for file in python_files:
            if 'venv' not in str(file) and '.tox' not in str(file):
                metrics = analyze_python_file(file)
                total_metrics = CodeMetrics(*(a + b for a, b in zip(total_metrics, metrics)))
        
        stats.update({
            'python_files': len(python_files),
            'classes': total_metrics.classes,
            'functions': total_metrics.functions,
            'try_statements': total_metrics.try_statements,
            'if_statements': total_metrics.if_statements,
            'total_lines': total_metrics.total_lines,
            'blank_lines': total_metrics.blank_lines,
            'comment_lines': total_metrics.comment_lines,
            'code_lines': total_metrics.total_lines - total_metrics.blank_lines - total_metrics.comment_lines
        })
    
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
        if 'python_files' in python_stats:
            print(f"  Python Files:       {python_stats['python_files']}")
        if 'classes' in python_stats:
            print(f"  Classes:           {python_stats['classes']}")
        if 'functions' in python_stats:
            print(f"  Functions:         {python_stats['functions']}")
        if 'try_statements' in python_stats:
            print(f"  Try Statements:    {python_stats['try_statements']}")
        if 'if_statements' in python_stats:
            print(f"  If Statements:     {python_stats['if_statements']}")
        if 'total_lines' in python_stats:
            print(f"  Total Lines:       {python_stats['total_lines']}")
        if 'blank_lines' in python_stats:
            print(f"  Blank Lines:       {python_stats['blank_lines']}")
        if 'comment_lines' in python_stats:
            print(f"  Comment Lines:     {python_stats['comment_lines']}")
        if 'code_lines' in python_stats:
            print(f"  Code Lines:        {python_stats['code_lines']}")
        if 'coverage' in python_stats:
            print(f"  Test Coverage:     {python_stats['coverage']}%")
        if 'dependencies' in python_stats:
            print(f"  Dependencies:      {python_stats['dependencies']}")
        if 'dev_dependencies' in python_stats:
            print(f"  Dev Dependencies:  {python_stats['dev_dependencies']}")

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