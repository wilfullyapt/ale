import pytest
from pathlib import Path
import yaml
import json
from tools.config import (
    ConfigFile,
    find_config_dir,
    load_config,
    save_config,
    get_managed_configs,
    validate_config
)

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def config_dir(temp_dir):
    config_dir = temp_dir / '.ale' / 'config'
    config_dir.mkdir(parents=True)
    return config_dir

@pytest.fixture
def yaml_config(temp_dir):
    config = {
        'name': 'test-project',
        'version': '1.0.0',
        'dependencies': ['pytest', 'pyyaml']
    }
    config_file = temp_dir / 'test.yaml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    return config_file

@pytest.fixture
def json_config(temp_dir):
    config = {
        'name': 'test-project',
        'version': '1.0.0',
        'dependencies': ['jest', 'typescript']
    }
    config_file = temp_dir / 'test.json'
    with open(config_file, 'w') as f:
        json.dump(config, f)
    return config_file

def test_find_config_dir(config_dir, monkeypatch):
    monkeypatch.chdir(config_dir.parent.parent)
    assert find_config_dir() == config_dir

def test_load_config_yaml(yaml_config):
    config = load_config(yaml_config)
    assert config['name'] == 'test-project'
    assert config['version'] == '1.0.0'
    assert 'pytest' in config['dependencies']

def test_load_config_json(json_config):
    config = load_config(json_config)
    assert config['name'] == 'test-project'
    assert config['version'] == '1.0.0'
    assert 'jest' in config['dependencies']

def test_load_config_invalid_format(temp_dir):
    invalid_file = temp_dir / 'test.txt'
    invalid_file.touch()
    with pytest.raises(ValueError, match='Unsupported file format'):
        load_config(invalid_file)

def test_save_config_yaml(temp_dir):
    config = {
        'name': 'new-project',
        'version': '2.0.0'
    }
    output_file = temp_dir / 'output.yaml'
    save_config(config, output_file)
    
    loaded_config = load_config(output_file)
    assert loaded_config == config

def test_save_config_json(temp_dir):
    config = {
        'name': 'new-project',
        'version': '2.0.0'
    }
    output_file = temp_dir / 'output.json'
    save_config(config, output_file)
    
    loaded_config = load_config(output_file)
    assert loaded_config == config

def test_get_managed_configs(config_dir):
    # Create a template
    template_dir = config_dir / 'templates'
    template_dir.mkdir()
    template_file = template_dir / 'tsconfig.json.template'
    template_file.touch()
    
    configs = get_managed_configs()
    
    assert 'python' in configs
    assert 'typescript' in configs
    assert configs['typescript'].path.name == 'tsconfig.json'
    assert configs['typescript'].template == template_file

def test_validate_config_no_schema():
    config = {'name': 'test'}
    assert validate_config(config) is True

def test_validate_config_with_schema(temp_dir):
    schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'version': {'type': 'string'}
        },
        'required': ['name', 'version']
    }
    schema_file = temp_dir / 'test.schema.json'
    with open(schema_file, 'w') as f:
        json.dump(schema, f)
    
    # Valid config
    valid_config = {'name': 'test', 'version': '1.0.0'}
    assert validate_config(valid_config, schema_file) is True
    
    # Invalid config
    invalid_config = {'name': 'test'}  # missing required version
    assert validate_config(invalid_config, schema_file) is False