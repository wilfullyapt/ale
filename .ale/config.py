#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

def parse_args():
    parser = argparse.ArgumentParser(description='Manage configuration settings')
    parser.add_argument('--get', help='Get a configuration value')
    parser.add_argument('--set', help='Set a configuration value')
    parser.add_argument('--value', help='Value to set (required with --set)')
    parser.add_argument('--delete', help='Delete a configuration value')
    parser.add_argument('--list', action='store_true', help='List all configuration values')
    return parser.parse_args()

class Config:
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON in {self.config_file}")
                self.config = {}

    def save(self) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str) -> Optional[Any]:
        return self.config.get(key)

    def set(self, key: str, value: Any) -> None:
        try:
            # Try to parse as JSON if it's a string
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
            self.config[key] = value
            self.save()
        except Exception as e:
            print(f"Error setting configuration: {e}")

    def delete(self, key: str) -> None:
        if key in self.config:
            del self.config[key]
            self.save()

    def list_all(self) -> Dict[str, Any]:
        return self.config

def main():
    args = parse_args()
    config = Config(Path.home() / '.config' / 'ale' / 'config.json')

    if args.get:
        value = config.get(args.get)
        if value is not None:
            print(json.dumps(value))
        else:
            print(f"No value found for key: {args.get}")
            exit(1)

    elif args.set:
        if args.value is None:
            print("Error: --value is required with --set")
            exit(1)
        config.set(args.set, args.value)
        print(f"Set {args.set} = {args.value}")

    elif args.delete:
        config.delete(args.delete)
        print(f"Deleted {args.delete}")

    elif args.list:
        settings = config.list_all()
        if settings:
            print(json.dumps(settings, indent=2))
        else:
            print("No configuration settings found")

    else:
        print("Error: No action specified. Use --help for usage information.")
        exit(1)

if __name__ == '__main__':
    main()