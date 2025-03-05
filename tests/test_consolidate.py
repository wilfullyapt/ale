import pytest
from pathlib import Path
import yaml
from tools.consolidate import (
    ConsolidateConfig,
    parse_args,
    read_yaml_config,
    should_ignore,
    get_files_per_output,
    pricol
)

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def consolidate_config():
    return ConsolidateConfig(
        dir="test_dir",
        output_dir="test_output",
        recursive=True,
        dry_run=False,
        ignore=True
    )

@pytest.fixture
def yaml_config(temp_dir):
    config = {
        'frontend': {
            'files': [
                'src/components/Button.tsx',
                'src/components/Input.tsx'
            ],
            'ignore': [
                '*.test.tsx',
                '*.spec.tsx'
            ]
        },
        'backend': {
            'files': [
                'src/models/user.py',
                'src/models/auth.py'
            ],
            'ignore': [
                '*.pyc',
                '__pycache__/*'
            ]
        }
    }
    
    config_file = temp_dir / 'consolidate.yaml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file

def test_consolidate_config_defaults():
    config = ConsolidateConfig()
    assert config.dir == "."
    assert config.output_dir == "consolidations"
    assert config.recursive is False
    assert config.dry_run is False
    assert config.ignore is True

def test_parse_args(monkeypatch):
    test_args = ['--dir', 'test_dir', '--output-dir', 'test_output', '--recursive']
    monkeypatch.setattr('sys.argv', ['consolidate.py'] + test_args)
    
    config = parse_args()
    assert config.dir == 'test_dir'
    assert config.output_dir == 'test_output'
    assert config.recursive is True
    assert config.dry_run is False
    assert config.ignore is True

def test_read_yaml_config(yaml_config, monkeypatch):
    monkeypatch.setattr('tools.consolidate.__file__', str(yaml_config))
    
    config = read_yaml_config()
    assert 'frontend' in config
    assert 'backend' in config
    assert len(config['frontend']['files']) == 2
    assert len(config['backend']['files']) == 2

def test_should_ignore():
    patterns = ['*.test.tsx', '*.spec.tsx', '__pycache__/*']
    
    assert should_ignore('component.test.tsx', patterns) is True
    assert should_ignore('component.spec.tsx', patterns) is True
    assert should_ignore('__pycache__/module.pyc', patterns) is True
    assert should_ignore('component.tsx', patterns) is False
    assert should_ignore('module.py', patterns) is False

def test_get_files_per_output(temp_dir, consolidate_config, monkeypatch):
    # Create test directory structure
    test_dir = temp_dir / 'test_dir'
    test_dir.mkdir()
    
    # Create test files
    files = [
        'src/components/Button.tsx',
        'src/components/Input.tsx',
        'src/components/Button.test.tsx',  # Should be ignored
        'src/models/user.py',
        'src/models/auth.py',
        'src/models/__pycache__/user.pyc'  # Should be ignored
    ]
    
    for file in files:
        file_path = test_dir / file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
    
    # Create config
    config = {
        'test_dir': {
            'files': [
                'src/components/Button.tsx',
                'src/components/Input.tsx',
                'src/components/Button.test.tsx',
                'src/models/user.py',
                'src/models/auth.py',
                'src/models/__pycache__/user.pyc'
            ],
            'ignore': [
                '*.test.tsx',
                '__pycache__/*'
            ]
        }
    }
    
    monkeypatch.setattr('tools.consolidate.__file__', str(test_dir / 'script.py'))
    
    files_map = get_files_per_output(consolidate_config, config)
    
    assert len(files_map) == 4  # Two files should be ignored
    assert any('Button.tsx' in str(p) for p in files_map.values())
    assert any('Input.tsx' in str(p) for p in files_map.values())
    assert any('user.py' in str(p) for p in files_map.values())
    assert any('auth.py' in str(p) for p in files_map.values())
    assert not any('Button.test.tsx' in str(p) for p in files_map.values())
    assert not any('user.pyc' in str(p) for p in files_map.values())

def test_pricol(capsys):
    test_text = "Test message"
    
    # Test with default color
    pricol(test_text)
    captured = capsys.readouterr()
    assert test_text in captured.out
    
    # Test with specific color
    pricol(test_text, color="red")
    captured = capsys.readouterr()
    assert test_text in captured.out
    assert "\033[31m" in captured.out  # Red color code
    
    # Test with invalid color (should default to white)
    pricol(test_text, color="invalid")
    captured = capsys.readouterr()
    assert test_text in captured.out
    assert "\033[37m" in captured.out  # White color code