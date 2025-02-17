#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
import shutil
from typing import Dict, Any, Optional
import yaml
import json
from dataclasses import dataclass

@dataclass
class ConfigFile:
    path: Path
    format: str  # 'yaml' or 'json'
    template: Optional[Path] = None

def find_config_dir() -> Optional[Path]:
    """Find .ale/config directory"""
    current_dir = Path.cwd()
    config_dir = current_dir / '.ale' / 'config'
    return config_dir if config_dir.is_dir() else None

def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from file"""
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

def save_config(config: Dict[str, Any], path: Path) -> None:
    """Save configuration to file"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        if path.suffix in ['.yaml', '.yml']:
            yaml.dump(config, f, default_flow_style=False)
        elif path.suffix == '.json':
            json.dump(config, f, indent=2)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

def get_managed_configs() -> Dict[str, ConfigFile]:
    """Get list of managed configuration files"""
    configs = {
        'python': ConfigFile(
            Path('pyproject.toml'),
            'toml'
        ),
        'typescript': ConfigFile(
            Path('tsconfig.json'),
            'json'
        ),
        'eslint': ConfigFile(
            Path('.eslintrc.json'),
            'json'
        ),
        'prettier': ConfigFile(
            Path('.prettierrc'),
            'json'
        ),
        'jest': ConfigFile(
            Path('jest.config.js'),
            'js'
        ),
        'docker': ConfigFile(
            Path('docker-compose.yml'),
            'yaml'
        ),
        'github-actions': ConfigFile(
            Path('.github/workflows/ci.yml'),
            'yaml'
        )
    }
    
    # Look for templates in .ale/config/templates
    config_dir = find_config_dir()
    if config_dir:
        template_dir = config_dir / 'templates'
        if template_dir.is_dir():
            for config in configs.values():
                template = template_dir / f"{config.path.name}.template"
                if template.is_file():
                    config.template = template
    
    return configs

def validate_config(config: Dict[str, Any], schema_path: Optional[Path] = None) -> bool:
    """Validate configuration against schema"""
    if not schema_path or not schema_path.is_file():
        return True  # No schema to validate against
        
    try:
        import jsonschema
        schema = load_config(schema_path)
        jsonschema.validate(config, schema)
        return True
    except ImportError:
        print("Warning: jsonschema package not installed, skipping validation",
              file=sys.stderr)
        return True
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return False

def main() -> int:
    parser = argparse.ArgumentParser(description='ALE Configuration Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List managed configurations')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show configuration contents')
    show_parser.add_argument('name', help='Configuration name')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize configuration')
    init_parser.add_argument('name', help='Configuration name')
    init_parser.add_argument('--force', action='store_true',
                            help='Overwrite existing configuration')

    # Validate command
    validate_parser = subparsers.add_parser('validate', 
                                          help='Validate configuration')
    validate_parser.add_argument('name', help='Configuration name')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    configs = get_managed_configs()

    if args.command == 'list':
        print("\nManaged Configurations:")
        for name, config in configs.items():
            status = "✓" if config.path.exists() else " "
            template = " (has template)" if config.template else ""
            print(f"  [{status}] {name}: {config.path}{template}")
        return 0

    if args.command in ['show', 'init', 'validate']:
        if args.name not in configs:
            print(f"Error: Unknown configuration '{args.name}'", file=sys.stderr)
            print("\nAvailable configurations:")
            for name in configs:
                print(f"  {name}")
            return 1

        config_file = configs[args.name]

        if args.command == 'show':
            if not config_file.path.is_file():
                print(f"Configuration file not found: {config_file.path}")
                return 1
            try:
                config = load_config(config_file.path)
                if config_file.format == 'yaml':
                    print(yaml.dump(config, default_flow_style=False))
                else:
                    print(json.dumps(config, indent=2))
                return 0
            except Exception as e:
                print(f"Error reading configuration: {e}", file=sys.stderr)
                return 1

        elif args.command == 'init':
            if config_file.path.exists() and not args.force:
                print(f"Configuration file already exists: {config_file.path}")
                print("Use --force to overwrite")
                return 1

            if config_file.template:
                try:
                    shutil.copy2(config_file.template, config_file.path)
                    print(f"Initialized {args.name} configuration from template")
                    return 0
                except Exception as e:
                    print(f"Error copying template: {e}", file=sys.stderr)
                    return 1
            else:
                print(f"No template found for {args.name} configuration")
                return 1

        elif args.command == 'validate':
            if not config_file.path.is_file():
                print(f"Configuration file not found: {config_file.path}")
                return 1

            config_dir = find_config_dir()
            schema_path = None
            if config_dir:
                schema_path = config_dir / 'schemas' / f"{args.name}.schema.json"

            try:
                config = load_config(config_file.path)
                if validate_config(config, schema_path):
                    print(f"Configuration is valid")
                    return 0
                else:
                    print(f"Configuration is invalid")
                    return 1
            except Exception as e:
                print(f"Error validating configuration: {e}", file=sys.stderr)
                return 1

    return 1

if __name__ == '__main__':
    sys.exit(main())