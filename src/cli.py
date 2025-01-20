import sys
import subprocess
from pathlib import Path
from typing import List, Optional

def find_ale_directory() -> Optional[Path]:
    """
    Find the .ale directory in the current working directory.
    Returns None if not found.
    """
    current_dir = Path.cwd()
    ale_dir = current_dir / '.ale'

    return ale_dir if ale_dir.is_dir() else None

def run_command(script_path: Path, args: List[str]) -> int:
    """
    Run the specified script with given arguments.
    Returns the exit code from the script execution.
    """
    if script_path.suffix == '.py':
        command = [sys.executable, str(script_path)] + args
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
    if len(sys.argv) < 2:
        print("Usage: ale script_name [arg1 [arg2 ...]]", file=sys.stderr)
        return 1

    ale_dir = find_ale_directory()
    if not ale_dir:
        print("Error: No .ale directory found in current working directory", file=sys.stderr)
        return 1

    script_name = sys.argv[1]
    script_path = ale_dir / script_name

    if not script_path.exists():
        print(f"Error: Script '{script_name}' not found in .ale directory", file=sys.stderr)
        return 1

    if not script_path.is_file():
        print(f"Error: '{script_name}' is not a file", file=sys.stderr)
        return 1

    return run_command(script_path, sys.argv[2:])
