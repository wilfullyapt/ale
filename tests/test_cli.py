import pytest
import os
import sys
from pathlib import Path
from ale.cli import find_ale_directory, run_command, main

def test_find_ale_directory(tmp_path):
    # Test when .ale directory exists
    ale_dir = tmp_path / '.ale'
    ale_dir.mkdir()
    os.chdir(tmp_path)
    assert find_ale_directory() == ale_dir

    # Test when .ale directory doesn't exist
    ale_dir.rmdir()
    assert find_ale_directory() is None

def test_run_command(tmp_path):
    # Create a test Python script
    ale_dir = tmp_path / '.ale'
    ale_dir.mkdir()
    test_script = ale_dir / 'test.py'
    test_script.write_text('print("Hello, World!")')
    
    result = run_command(test_script, [])
    assert result == 0
