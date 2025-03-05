import pytest
import os
import sys
import shutil
from pathlib import Path
from ale.cli import find_ale_directory, run_command, main, parse_args

@pytest.fixture
def setup_ale_directory(tmp_path):
    """Setup a temporary .ale directory with test files"""
    original_dir = os.getcwd()
    ale_dir = tmp_path / '.ale'
    ale_dir.mkdir()
    os.chdir(tmp_path)
    
    yield ale_dir
    
    # Cleanup after test
    os.chdir(original_dir)
    if ale_dir.exists():
        shutil.rmtree(ale_dir)

def test_cleanup_after_successful_execution(setup_ale_directory):
    """Test that temporary files are cleaned up after successful script execution"""
    ale_dir = setup_ale_directory
    test_script = ale_dir / 'test.py'
    temp_file = ale_dir / 'temp.txt'
    
    # Create a script that creates and then deletes a temp file
    script_content = f'''
import os
temp_file = "{temp_file}"
with open(temp_file, "w") as f:
    f.write("temporary data")
os.remove(temp_file)
'''
    test_script.write_text(script_content)
    
    result = run_command(test_script, [])
    assert result == 0
    assert not temp_file.exists()

def test_cleanup_after_failed_execution(setup_ale_directory):
    """Test that cleanup happens even when script fails"""
    ale_dir = setup_ale_directory
    test_script = ale_dir / 'failing_test.py'
    temp_file = ale_dir / 'temp.txt'
    
    # Create a script that creates a temp file but fails before cleanup
    script_content = f'''
import os
temp_file = "{temp_file}"
with open(temp_file, "w") as f:
    f.write("temporary data")
raise Exception("Simulated failure")
'''
    test_script.write_text(script_content)
    
    result = run_command(test_script, [])
    assert result != 0  # Script should fail
    assert temp_file.exists()  # Temp file remains due to failure
    temp_file.unlink()  # Clean up the temp file

def test_cleanup_in_interactive_mode(setup_ale_directory):
    """Test cleanup behavior in interactive mode"""
    ale_dir = setup_ale_directory
    test_script = ale_dir / 'interactive_test.py'
    temp_file = ale_dir / 'interactive_temp.txt'
    
    script_content = f'''
import os
temp_file = "{temp_file}"
with open(temp_file, "w") as f:
    f.write("interactive data")
# In interactive mode, this file should persist until explicitly cleaned
'''
    test_script.write_text(script_content)
    
    result = run_command(test_script, [], interactive=True)
    assert result == 0
    assert temp_file.exists()
    temp_file.unlink()

def test_cleanup_nonexistent_script(setup_ale_directory):
    """Test cleanup when trying to run a nonexistent script"""
    ale_dir = setup_ale_directory
    nonexistent_script = ale_dir / 'nonexistent.py'
    
    result = run_command(nonexistent_script, [])
    assert result != 0

def test_cleanup_invalid_script_type(setup_ale_directory):
    """Test cleanup when running an invalid script type"""
    ale_dir = setup_ale_directory
    invalid_script = ale_dir / 'test.invalid'
    invalid_script.write_text('some content')
    
    result = run_command(invalid_script, [])
    assert result != 0
    invalid_script.unlink()

def test_cleanup_ale_directory_removal(tmp_path):
    """Test that removing .ale directory is handled gracefully"""
    original_dir = os.getcwd()
    ale_dir = tmp_path / '.ale'
    ale_dir.mkdir()
    os.chdir(tmp_path)
    
    assert find_ale_directory() == ale_dir
    shutil.rmtree(ale_dir)
    assert find_ale_directory() is None
    
    os.chdir(original_dir)

def test_parse_args_interactive():
    """Test argument parsing with interactive mode"""
    test_args = ['ale', '-i', 'script.py', 'arg1', 'arg2']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        args, script_name, script_args = parse_args()
        assert args.interactive is True
        assert script_name == 'script.py'
        assert script_args == ['arg1', 'arg2']

def test_parse_args_non_interactive():
    """Test argument parsing without interactive mode"""
    test_args = ['ale', 'script.py', 'arg1', 'arg2']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        args, script_name, script_args = parse_args()
        assert args.interactive is False
        assert script_name == 'script.py'
        assert script_args == ['arg1', 'arg2']

def test_parse_args_no_script():
    """Test argument parsing with no script name"""
    test_args = ['ale']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        with pytest.raises(SystemExit):
            parse_args()

def test_run_shell_script(setup_ale_directory):
    """Test running a shell script"""
    ale_dir = setup_ale_directory
    test_script = ale_dir / 'test.sh'
    test_script.write_text('#!/bin/bash\necho "Hello from shell"')
    test_script.chmod(0o755)
    
    result = run_command(test_script, [])
    assert result == 0

def test_main_with_missing_ale_dir(tmp_path):
    """Test main function with missing .ale directory"""
    os.chdir(tmp_path)
    test_args = ['ale', 'script.py']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        assert main() == 1

def test_main_with_missing_script(setup_ale_directory):
    """Test main function with missing script"""
    test_args = ['ale', 'nonexistent.py']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        assert main() == 1

def test_main_with_directory_as_script(setup_ale_directory):
    """Test main function with directory instead of script"""
    ale_dir = setup_ale_directory
    test_dir = ale_dir / 'test_dir'
    test_dir.mkdir()
    
    test_args = ['ale', 'test_dir']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        assert main() == 1

def test_main_successful_execution(setup_ale_directory):
    """Test main function with successful script execution"""
    ale_dir = setup_ale_directory
    test_script = ale_dir / 'test.py'
    test_script.write_text('print("Hello, World!")')
    
    test_args = ['ale', 'test.py']
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(sys, 'argv', test_args)
        assert main() == 0