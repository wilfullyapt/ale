from dataclasses import dataclass
from typing import Any, Dict
from pathlib import Path
import argparse
import shutil

import yaml

def pricol(text: str, color: str = "white") -> None:
    """
    Print colored text using ANSI escape codes.
    Available colors: black, red, green, yellow, blue, magenta, cyan, white
    """
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m"
    }
    reset = "\033[0m"
    
    color_code = colors.get(color.lower(), colors["white"])
    print(f"{color_code}{text}{reset}")


@dataclass
class ConsolidateConfig:
    """Configuration for consolidation process"""
    dir: str = "."
    output_dir: str = 'consolidations'
    recursive: bool = False
    dry_run: bool = False

def parse_args() -> ConsolidateConfig:
    """Parse command line arguments and return a ConsolidateConfig instance"""
    parser = argparse.ArgumentParser(description='Consolidate files tool')

    parser.add_argument('--dir', '-i',
                       default=".",
                       help='Input path to process (default: current directory)')

    parser.add_argument('--output-dir', '-o',
                       help='Output path for consolidated files')

    parser.add_argument('--recursive', '-r',
                       action='store_true',
                       help='Process directories recursively')

    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be done without making changes')

    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = 'consolidations'

    return ConsolidateConfig(
        dir=args.dir,
        output_dir=args.output_dir,
        recursive=args.recursive,
        dry_run=args.dry_run
    )

def read_yaml_config() -> Dict[str, Any]:
    """ Read in local YAML file and return contents """
    ref = Path(__file__)
    config_path = ref.parent / f"{ref.stem}-example.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}")

def get_files_per_output(config, files):
    """ Returns a key, value pair Dict for files to copy """
    working_dir = Path.cwd() / config.dir
    if not working_dir.is_dir():
        raise NotADirectoryError(f"Directory not found: {working_dir}")

    if config.dir in files:
        files = files[config.dir]
    else:
        files = [ f"{dir}/{file_path}" for dir in files for file_path in files[dir] ]
    return { file.replace('/', '.') : working_dir/file for file in files }

if __name__ == '__main__':
    """
    With ALE installed, try these commands:
        - ale consolidate.py --dir=frontend
        - ale consolidate.py
           ^          ^
           |         script in `.ale` dir to run
        `pip install -e(ditible) .` from ale project

    Example consolidate.yaml file:
        backend:
          - src/auth.py
          - src/database_models.py
          - src/main.py
        frontend:
          - app/auth/login/page.tsx
          - app/auth/signup/page.tsx

    Copy files easily with intact tree representation
    """
    config = parse_args()
    files = read_yaml_config()

    files = get_files_per_output(config, files)
    output_dir = Path.cwd() / config.output_dir

    # Reduce String lambda
    rs = lambda s: str(s.relative_to(Path.cwd()) if str(s).startswith(str(Path.cwd())) else s)

    if config.dry_run is False:
        if output_dir.is_dir():
            shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir.mkdir(parents=True, exist_ok=False)

    for file, filepath in files.items():

        if filepath.is_file():
            output_file = output_dir / file

            if config.dry_run:
                pricol(f"Would copy {rs(filepath)} to {rs(output_file)}", color="yellow")
            else:
                try:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(filepath, output_file)
                    pricol(f"Successfully copied {rs(filepath)} to {rs(output_file)}", color="green")
                except Exception as e:
                    pricol(f"Error copying {filepath}: {e}", color="red")
        else:
            pricol(f"{rs(filepath)} isn't a file", color='red')

