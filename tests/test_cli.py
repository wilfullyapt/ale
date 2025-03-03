import pytest
import os
import sys
import shutil
from pathlib import Path
from ale.cli import find_script_path, run_command, init_ale_directory, get_tool_docs, parse_args

def test_find_script_path(tmp_path):
    # Setup test environment
    os.chdir(tmp_path)
    ale_dir = tmp_path / '.ale'
    ale_dir.mkdir()
    
    # Test finding script in .ale directory
    local_script = ale_dir / 'test.py'
    local_script.write_text('print("test")')
    assert find_script_path('test.py') == local_script
    
    # Test finding script in tools directory
    tools_dir = Path(__file__).parent.parent / 'tools'
    if tools_dir.exists():
        for script in tools_dir.glob('*.py'):
            if not script.name.startswith('_'):
                assert find_script_path(script.name) == script
                break
    
    # Test script not found
    assert find_script_path('nonexistent.py') is None

def test_init_ale_directory(tmp_path):
    # Setup test environment
    os.chdir(tmp_path)
    
    # Test successful initialization
    assert init_ale_directory() == 0
    assert (tmp_path / '.ale').is_dir()
    
    # Test initialization when directory already exists
    assert init_ale_directory() == 1

def test_run_command(tmp_path):
    # Create a test Python script
    script_path = tmp_path / 'test.py'
    script_path.write_text('print("Hello, World!")')
    
    # Test running Python script
    result = run_command(script_path, [])
    assert result == 0
    
    # Test running Python script with arguments
    script_path.write_text('import sys; print(sys.argv[1])')
    result = run_command(script_path, ['test_arg'])
    assert result == 0
    
    # Test running non-existent script
    result = run_command(tmp_path / 'nonexistent.py', [])
    assert result == 2  # Python returns exit code 2 for file not found

def test_parse_args(monkeypatch):
    # Test help command
    monkeypatch.setattr(sys, 'argv', ['ale'])
    with pytest.raises(SystemExit) as exc_info:
        parse_args()
    assert exc_info.value.code == 1
    
    # Test script command
    test_args = ['ale', '-i', 'script.py', 'arg1', 'arg2']
    monkeypatch.setattr(sys, 'argv', test_args)
    args, script_name, script_args = parse_args()
    assert args.interactive is True
    assert script_name == 'script.py'
    assert script_args == ['arg1', 'arg2']

def test_get_tool_docs(tmp_path):
    # Create a test tools directory with a test script
    tools_dir = tmp_path / 'tools'
    tools_dir.mkdir()
    test_script = tools_dir / 'test_tool.py'
    test_script.write_text('''"""
Test tool documentation.
"""
def main():
    pass
''')
    
    # Temporarily replace the tools directory
    original_tools = Path(__file__).parent.parent / 'tools'
    if original_tools.exists():
        shutil.move(str(original_tools), str(original_tools) + '.bak')
    shutil.copytree(str(tools_dir), str(original_tools))
    
    try:
        docs = get_tool_docs()
        assert 'test_tool' in docs
        assert docs['test_tool'].strip() == 'Test tool documentation.'
    finally:
        # Restore original tools directory
        shutil.rmtree(str(original_tools))
        if (original_tools.parent / (original_tools.name + '.bak')).exists():
            shutil.move(str(original_tools) + '.bak', str(original_tools))
