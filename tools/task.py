#!/usr/bin/env python3
"""
Task runner for executing project-specific tasks and commands.

This tool helps manage and execute project tasks defined in a YAML
configuration file, supporting dependencies, environment variables,
and command sequences.

Features:
- Task dependencies
- Environment variable support
- Dry-run mode
- Task listing and documentation
- Error handling and reporting
"""
import sys
import os
import argparse
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Any
import shlex
from dataclasses import dataclass

import yaml

@dataclass
class TaskConfig:
    """Configuration for task execution"""
    dry_run: bool = False
    env: Dict[str, str] = None

def find_tasks_file() -> Optional[Path]:
    """Find tasks.yaml in .ale directory"""
    current_dir = Path.cwd()
    tasks_file = current_dir / '.ale' / 'tasks.yaml'
    return tasks_file if tasks_file.is_file() else None

def load_tasks() -> Dict[str, Any]:
    """Load tasks from tasks.yaml"""
    tasks_file = find_tasks_file()
    if not tasks_file:
        print("Error: No tasks.yaml found in .ale directory", file=sys.stderr)
        sys.exit(1)

    try:
        with open(tasks_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading tasks.yaml: {e}", file=sys.stderr)
        sys.exit(1)

def execute_task(name: str, task_def: Dict[str, Any], config: TaskConfig, visited: set = None) -> int:
    """Execute a task and its dependencies"""
    if visited is None:
        visited = set()

    if name in visited:
        print(f"Error: Circular dependency detected for task '{name}'", file=sys.stderr)
        return 1

    visited.add(name)

    # Execute dependencies first
    deps = task_def.get('deps', [])
    for dep in deps:
        if dep not in tasks:
            print(f"Error: Dependency '{dep}' not found for task '{name}'", file=sys.stderr)
            return 1
        result = execute_task(dep, tasks[dep], config, visited)
        if result != 0:
            return result

    # Get task details
    commands = task_def.get('run', [])
    if isinstance(commands, str):
        commands = [commands]

    description = task_def.get('description', '')
    if description:
        print(f"\n=== {name}: {description} ===")
    else:
        print(f"\n=== Running task: {name} ===")

    # Set up environment
    env = os.environ.copy()
    if config.env:
        env.update(config.env)
    task_env = task_def.get('env', {})
    env.update(task_env)

    # Execute commands
    for cmd in commands:
        print(f"$ {cmd}")
        if config.dry_run:
            continue

        try:
            # Split command properly handling quotes
            cmd_parts = shlex.split(cmd)
            result = subprocess.run(cmd_parts, env=env)
            if result.returncode != 0:
                print(f"Error: Command '{cmd}' failed with code {result.returncode}", 
                      file=sys.stderr)
                return result.returncode
        except Exception as e:
            print(f"Error executing command '{cmd}': {e}", file=sys.stderr)
            return 1

    return 0

def list_tasks(tasks: Dict[str, Any]) -> None:
    """Display available tasks and their descriptions"""
    print("\nAvailable tasks:")
    for name, task in sorted(tasks.items()):
        desc = task.get('description', 'No description')
        deps = task.get('deps', [])
        deps_str = f" (deps: {', '.join(deps)})" if deps else ""
        print(f"  {name}: {desc}{deps_str}")

def main() -> int:
    parser = argparse.ArgumentParser(description='ALE Task Runner')
    parser.add_argument('command', choices=['run', 'list'],
                       help='Command to execute')
    parser.add_argument('task', nargs='?',
                       help='Task to run (required for run command)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show commands without executing them')
    parser.add_argument('-e', '--env', action='append',
                       help='Set environment variables (KEY=VALUE)')
    
    args = parser.parse_args()

    # Load tasks
    global tasks
    tasks = load_tasks()

    if args.command == 'list':
        list_tasks(tasks)
        return 0

    if not args.task:
        print("Error: Task name required for 'run' command", file=sys.stderr)
        return 1

    if args.task not in tasks:
        print(f"Error: Task '{args.task}' not found", file=sys.stderr)
        print("\nAvailable tasks:")
        list_tasks(tasks)
        return 1

    # Parse environment variables
    env = {}
    if args.env:
        for env_var in args.env:
            try:
                key, value = env_var.split('=', 1)
                env[key] = value
            except ValueError:
                print(f"Error: Invalid environment variable format: {env_var}", 
                      file=sys.stderr)
                return 1

    config = TaskConfig(dry_run=args.dry_run, env=env)
    return execute_task(args.task, tasks[args.task], config)

if __name__ == '__main__':
    sys.exit(main())