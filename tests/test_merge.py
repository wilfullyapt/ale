import os
import shutil
from pathlib import Path
import pytest
from tools.merge import (
    find_ale_directory,
    get_mirror_directory,
    collect_files,
    files_are_identical,
    merge_directories
)

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure"""
    project_dir = tmp_path / "myproject"
    ale_dir = project_dir / ".ale"
    mirror_dir = ale_dir / "myproject"
    
    # Create directories
    project_dir.mkdir()
    ale_dir.mkdir()
    mirror_dir.mkdir()
    
    return project_dir, ale_dir, mirror_dir

def test_find_ale_directory(temp_project):
    project_dir, ale_dir, _ = temp_project
    os.chdir(project_dir)
    assert find_ale_directory() == ale_dir

def test_get_mirror_directory(temp_project):
    _, ale_dir, mirror_dir = temp_project
    assert get_mirror_directory(ale_dir) == mirror_dir

def test_collect_files(temp_project):
    project_dir, _, _ = temp_project
    
    # Create some test files
    (project_dir / "file1.txt").write_text("test1")
    (project_dir / "file2.py").write_text("test2")
    subdir = project_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("test3")
    
    files = collect_files(project_dir)
    assert len(files) == 3
    assert Path("file1.txt") in files
    assert Path("file2.py") in files
    assert Path("subdir/file3.txt") in files

def test_files_are_identical(temp_project):
    project_dir, _, _ = temp_project
    
    file1 = project_dir / "test1.txt"
    file2 = project_dir / "test2.txt"
    file3 = project_dir / "test3.txt"
    
    file1.write_text("test content")
    file2.write_text("test content")
    file3.write_text("different content")
    
    assert files_are_identical(file1, file2)
    assert not files_are_identical(file1, file3)
    assert not files_are_identical(file1, project_dir / "nonexistent.txt")

def test_merge_directories(temp_project):
    project_dir, _, mirror_dir = temp_project
    
    # Create files in mirror
    (mirror_dir / "file1.txt").write_text("mirror1")
    subdir = mirror_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("mirror2")
    
    # Create different version in project
    (project_dir / "file1.txt").write_text("project1")
    
    # Test dry run
    merge_directories(project_dir, mirror_dir, dry_run=True)
    assert (project_dir / "file1.txt").read_text() == "project1"
    assert not (project_dir / "subdir/file2.txt").exists()
    
    # Test actual merge
    merge_directories(project_dir, mirror_dir)
    assert (project_dir / "file1.txt").read_text() == "mirror1"
    assert (project_dir / "subdir/file2.txt").read_text() == "mirror2"