import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional, Tuple

def find_script_path(script_name: str) -> Optional[Path]:
    """
    Find the script in either:
    1. Local .ale directory
    2. Package tools directory
    Returns None if not found in either location.
    """
    # First check local .ale directory
    current_dir = Path.cwd()
    local_ale_dir = current_dir / '.ale'
    if local_ale_dir.is_dir():
        script_path = local_ale_dir / script_name
        if script_path.is_file():
            return script_path

    # Then check package tools directory
    package_dir = Path(__file__).parent.parent
    tools_dir = package_dir / 'tools'
    if tools_dir.is_dir():
        script_path = tools_dir / script_name
        if script_path.is_file():
            return script_path

    return None

def parse_args() -> Tuple[argparse.Namespace, str, List[str]]:
    """
    Parse command line arguments.
    Returns tuple of (parsed_args, script_name, script_args)
    """
    parser = argparse.ArgumentParser(
        description='ALE command-line tool',
        usage='ale [-i] script_name [arg1 [arg2 ...]]'
    )
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Run Python scripts in interactive mode')

    args, remaining = parser.parse_known_args()

    if not remaining:
        parser.print_help()
        sys.exit(1)

    script_name = remaining[0]
    script_args = remaining[1:]

    return args, script_name, script_args

def run_command(script_path: Path, args: List[str], interactive: bool = False) -> int:
    """
    Run the specified script with given arguments.
    Returns the exit code from the script execution.
    """
    if script_path.suffix == '.py':
        command = [sys.executable]
        if interactive:
            command.append('-i')
        command.extend([str(script_path)] + args)
    elif script_path.suffix == '.sh':
        command = ['bash', str(script_path)] + args
    else:
        # For other executable files
        command = [str(script_path)] + args

    try:
        result = subprocess.run(command, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_path.name}: {e}", file=sys.stderr)
        return e.returncode
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def main() -> int:
    """
    Main entry point for the ALE command-line tool.
    Returns exit code.
    """
    args, script_name, script_args = parse_args()

    script_path = find_script_path(script_name)
    if not script_path:
        print(f"Error: Script '{script_name}' not found in .ale directory or tools directory", file=sys.stderr)
        return 1

    if not script_path.is_file():
        print(f"Error: '{script_name}' is not a file", file=sys.stderr)
        return 1

    return run_command(script_path, script_args, args.interactive)
