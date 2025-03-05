import os
from pathlib import Path
import pytest
from tools.stats import (
    count_files_by_type,
    get_file_sizes,
    format_size,
    get_git_stats,
    get_python_stats
)

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure"""
    project_dir = tmp_path / "myproject"
    project_dir.mkdir()
    return project_dir

def test_count_files_by_type(temp_project):
    # Create test files
    (temp_project / "file1.txt").write_text("test1")
    (temp_project / "file2.py").write_text("test2")
    (temp_project / "file3.py").write_text("test3")
    (temp_project / "noext").write_text("test4")
    
    counts = count_files_by_type(temp_project)
    assert counts['.txt'] == 1
    assert counts['.py'] == 2
    assert counts['(no extension)'] == 1

def test_get_file_sizes(temp_project):
    # Create test files with known sizes
    (temp_project / "file1.txt").write_text("a" * 100)
    (temp_project / "file2.py").write_text("b" * 200)
    (temp_project / "file3.py").write_text("c" * 300)
    
    sizes = get_file_sizes(temp_project)
    assert sizes['.txt'] == 100
    assert sizes['.py'] == 500  # 200 + 300

def test_format_size():
    assert format_size(100) == "100.0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"
    assert format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

def test_get_git_stats(temp_project):
    # Test when not in a git repo
    os.chdir(temp_project)
    stats = get_git_stats()
    assert stats == {}