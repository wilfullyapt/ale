#!/usr/bin/env python3
"""
Template management tool for creating and applying file templates.

This tool helps manage and apply file templates stored in the tools/templates
directory. Templates can contain variables (e.g., {{NAME}}) that will be
replaced when applying the template.

Features:
- List available templates
- Apply templates to new or existing files
- Support for variable substitution
- Automatic name extraction from file path
"""
import sys
import argparse
from pathlib import Path
import re
from typing import Dict, Optional

def find_template(name: str) -> Optional[Path]:
    """Find template file in tools/templates directory"""
    templates_dir = Path(__file__).parent / 'templates'
    template_file = templates_dir / f"{name}.txt"
    return template_file if template_file.is_file() else None

def list_templates() -> None:
    """List available templates"""
    templates_dir = Path(__file__).parent / 'templates'
    if not templates_dir.is_dir():
        print("No templates directory found", file=sys.stderr)
        return

    print("\nAvailable templates:")
    for template in templates_dir.glob('*.txt'):
        name = template.stem
        print(f"  {name}")

def apply_template(template_path: Path, output_path: Path, variables: Dict[str, str]) -> None:
    """Apply template with variables to output file"""
    with open(template_path, 'r') as f:
        content = f.read()

    # Replace variables in template
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", value)

    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Append to file if it exists, create if it doesn't
    mode = 'a' if output_path.exists() else 'w'
    with open(output_path, 'a') as f:
        if mode == 'a':
            f.write('\n\n')  # Add spacing if appending
        f.write(content)

def extract_name_from_path(path: str) -> str:
    """Extract name from file path for use in template"""
    return Path(path).stem

def main() -> int:
    parser = argparse.ArgumentParser(description='ALE Template Tool')
    parser.add_argument('template', nargs='?',
                       help='Template name to use')
    parser.add_argument('output', nargs='?',
                       help='Output file path')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List available templates')
    parser.add_argument('-v', '--var', action='append',
                       help='Set template variables (KEY=VALUE)')

    args = parser.parse_args()

    if args.list:
        list_templates()
        return 0

    if not args.template or not args.output:
        parser.print_help()
        return 1

    template_path = find_template(args.template)
    if not template_path:
        print(f"Error: Template '{args.template}' not found", file=sys.stderr)
        list_templates()
        return 1

    # Parse variables
    variables = {'NAME': extract_name_from_path(args.output)}
    if args.var:
        for var in args.var:
            try:
                key, value = var.split('=', 1)
                variables[key] = value
            except ValueError:
                print(f"Error: Invalid variable format: {var}", file=sys.stderr)
                return 1

    output_path = Path(args.output)
    try:
        apply_template(template_path, output_path, variables)
        action = "Updated" if output_path.exists() else "Created"
        print(f"{action} {output_path}")
        return 0
    except Exception as e:
        print(f"Error applying template: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())