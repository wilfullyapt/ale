import os
from pathlib import Path
import pytest
from tools.stats import (
    count_files_by_type,
    get_file_sizes,
    format_size,
    get_git_stats,
    get_python_stats,
    analyze_python_file,
    CodeMetrics
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

def test_analyze_python_file(temp_project):
    test_code = '''
class TestClass:
    def method1(self):
        try:
            if True:
                pass
            if False:
                pass
        except:
            pass

def standalone_function():
    pass

# This is a comment
'''
    test_file = temp_project / "test.py"
    test_file.write_text(test_code)
    
    metrics = analyze_python_file(test_file)
    assert isinstance(metrics, CodeMetrics)
    assert metrics.classes == 1
    assert metrics.functions == 2  # method1 and standalone_function
    assert metrics.try_statements == 1
    assert metrics.if_statements == 2
    assert metrics.total_lines == len(test_code.splitlines())
    assert metrics.blank_lines == 3  # Counting empty lines
    assert metrics.comment_lines == 1  # "# This is a comment"

def test_analyze_python_file_with_syntax_error(temp_project):
    test_file = temp_project / "bad.py"
    test_file.write_text("this is not valid python")
    
    metrics = analyze_python_file(test_file)
    assert isinstance(metrics, CodeMetrics)
    assert metrics.classes == 0
    assert metrics.functions == 0
    assert metrics.try_statements == 0
    assert metrics.if_statements == 0
    assert metrics.total_lines == 1
    assert metrics.blank_lines == 0
    assert metrics.comment_lines == 0