import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict

def find_ale_directory() -> Optional[Path]:
    """
    Find the .ale directory by traversing up from current directory.
    Returns None if not found.
    """
    current = Path.cwd()
    while current != current.parent:
        ale_dir = current / '.ale'
        if ale_dir.is_dir():
            return ale_dir
        current = current.parent
    return None

def find_script_path(script_name: str) -> Optional[Path]:
    """
    Find the script in either:
    1. Local .ale directory
    2. Package tools directory
    Returns None if not found in either location.
    """
    # First check local .ale directory
    local_ale_dir = find_ale_directory()
    if local_ale_dir:
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

def init_ale_directory() -> int:
    """
    Initialize .ale directory in current working directory.
    Returns exit code.
    """
    current_dir = Path.cwd()
    ale_dir = current_dir / '.ale'

    if ale_dir.exists():
        print("Error: .ale directory already exists", file=sys.stderr)
        return 1

    try:
        # Create .ale directory
        ale_dir.mkdir()
        
        # Copy example consolidation yaml
        package_dir = Path(__file__).parent.parent
        example_yaml = package_dir / 'tools' / 'consolidate-example.yaml'
        if example_yaml.exists():
            shutil.copy2(example_yaml, ale_dir / 'consolidate.yaml')
            print(f"Created .ale directory and copied consolidate.yaml")
            return 0
        else:
            print("Warning: Could not find example consolidate.yaml", file=sys.stderr)
            return 0
    except Exception as e:
        print(f"Error creating .ale directory: {e}", file=sys.stderr)
        return 1

def get_tool_docs() -> Dict[str, str]:
    """
    Get documentation for all tools by extracting their docstrings.
    Returns a dictionary of tool name to documentation.
    """
    tools_dir = Path(__file__).parent.parent / 'tools'
    docs = {}

    if not tools_dir.is_dir():
        return docs

    for tool_path in tools_dir.glob('*.py'):
        if tool_path.name.startswith('_'):
            continue

        try:
            # Read the file content
            with open(tool_path, 'r') as f:
                content = f.read()

            # Use ast to safely extract the docstring
            import ast
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)

            if docstring:
                # Clean up the docstring
                docs[tool_path.stem] = docstring.strip()
            else:
                # If no module docstring, try to get main() docstring
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef) and node.name == 'main':
                        if node.body and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Str):
                                docs[tool_path.stem] = node.body[0].value.s.strip()
                                break
        except Exception as e:
            print(f"Warning: Could not extract docs from {tool_path.name}: {e}", 
                  file=sys.stderr)

    return docs

def print_help() -> None:
    """Print detailed help information"""
    print("""ALE (Access Local Execution) - Project-specific CLI tool

Usage:
    ale [-i] <command> [args...]
    ale help                 Show this help message
    ale tools               List available tools and their documentation
    ale init                Initialize .ale directory in current directory
    ale <script> [args...]  Run a script from .ale or tools directory

Options:
    -i, --interactive       Run Python scripts in interactive mode

Commands:
    help     Show this help message
    tools    List available tools and their documentation
    init     Initialize .ale directory
    
Built-in Tools:
    template.py    Manage and apply file templates
    task.py       Run project-specific tasks
    cleanup.py    Clean project artifacts
    stats.py      Show project statistics
    config.py     Manage project configurations
    merge.py      Merge files from .ale mirror directory

Examples:
    # Initialize a new .ale directory
    ale init

    # Run a script with arguments
    ale script.py arg1 arg2

    # Run a built-in tool
    ale template.py list
    ale cleanup.py python
    ale stats.py

    # Run a Python script in interactive mode
    ale -i script.py

For more information about a specific tool:
    ale <tool_name> --help
""")

def print_tools() -> None:
    """Print available tools and their documentation"""
    docs = get_tool_docs()
    
    if not docs:
        print("No tools found or unable to read tool documentation.")
        return

    print("\nAvailable Tools:\n")
    
    for tool_name, doc in sorted(docs.items()):
        print(f"{tool_name}:")
        # Format the documentation
        if doc:
            # Split into lines and remove empty lines at start/end
            lines = [line.strip() for line in doc.split('\n')]
            lines = [line for line in lines if line]
            # Print first paragraph (stop at first empty line)
            for line in lines:
                if not line:
                    break
                print(f"    {line}")
        print()  # Empty line between tools

def parse_args() -> Tuple[argparse.Namespace, Optional[str], List[str]]:
    """
    Parse command line arguments.
    Returns tuple of (parsed_args, script_name, script_args)
    script_name can be None for built-in commands
    """
    parser = argparse.ArgumentParser(
        description='ALE command-line tool',
        usage='ale [-i] (help | tools | init | script_name [arg1 [arg2 ...]])'
    )
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Run Python scripts in interactive mode')

    args, remaining = parser.parse_known_args()

    if not remaining:
        print_help()
        sys.exit(1)

    command = remaining[0]
    
    # Handle built-in commands
    if command == 'help':
        print_help()
        sys.exit(0)
    elif command == 'tools':
        print_tools()
        sys.exit(0)
    elif command == 'init':
        return args, None, []

    return args, command, remaining[1:]

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

    # Handle built-in commands
    if script_name is None:
        return init_ale_directory()

    script_path = find_script_path(script_name)
    if not script_path:
        print(f"Error: Script '{script_name}' not found in .ale directory or tools directory", file=sys.stderr)
        return 1

    if not script_path.is_file():
        print(f"Error: '{script_name}' is not a file", file=sys.stderr)
        return 1

    return run_command(script_path, script_args, args.interactive)
