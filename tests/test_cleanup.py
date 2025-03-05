import pytest
from pathlib import Path
import yaml
from tools.cleanup import find_cleanup_config, load_config, find_matches, cleanup_paths

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def cleanup_config(temp_dir):
    config = {
        'python': {
            'description': 'Clean Python build artifacts',
            'patterns': [
                "**/__pycache__",
                "**/*.pyc",
                "**/*.pyo",
                "**/*.pyd",
                "**/.pytest_cache",
                "**/.coverage",
                "**/htmlcov",
                "build/",
                "dist/",
                "**/*.egg-info"
            ]
        },
        'temp': {
            'description': 'Clean temporary files',
            'patterns': ['*.tmp', '*.log']
        }
    }
    
    config_dir = temp_dir / '.ale'
    config_dir.mkdir(parents=True)
    config_file = config_dir / 'cleanup.yaml'
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file

def test_find_cleanup_config(temp_dir, cleanup_config, monkeypatch):
    monkeypatch.chdir(temp_dir)
    assert find_cleanup_config() == cleanup_config

def test_load_config(cleanup_config):
    config = load_config()
    assert 'python' in config
    assert 'temp' in config
    assert config['python']['patterns'] == [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.coverage",
        "**/htmlcov",
        "build/",
        "dist/",
        "**/*.egg-info"
    ]

def test_find_matches(temp_dir, monkeypatch):
    # Create test files
    test_files = [
        'test.pyc',
        'test.log',
        'src/__pycache__/module.pyc',
        'build/lib.py',
        'valid.py'
    ]
    
    for file in test_files:
        file_path = temp_dir / file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
    
    monkeypatch.chdir(temp_dir)
    
    # Test with Python patterns
    patterns = ['*.pyc', '__pycache__/*', 'build/*']
    matches = find_matches(patterns)
    assert len(matches) == 3
    assert any(str(m).endswith('test.pyc') for m in matches)
    assert any('__pycache__' in str(m) for m in matches)
    assert any('build' in str(m) for m in matches)
    
    # Test with temp patterns
    patterns = ['*.log']
    matches = find_matches(patterns)
    assert len(matches) == 1
    assert str(matches[0]).endswith('test.log')

def test_cleanup_paths(temp_dir, monkeypatch):
    # Create test files
    test_file = temp_dir / 'test.tmp'
    test_file.touch()
    test_dir = temp_dir / 'test_dir'
    test_dir.mkdir()
    (test_dir / 'file.txt').touch()
    
    monkeypatch.chdir(temp_dir)
    
    # Test dry run
    cleanup_paths([test_file, test_dir], dry_run=True)
    assert test_file.exists()
    assert test_dir.exists()
    
    # Test actual cleanup
    cleanup_paths([test_file, test_dir])
    assert not test_file.exists()
    assert not test_dir.exists()

