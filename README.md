# Access Local Execution (ALE)

[![Tests & Coverage](https://github.com/wilfullyapt/ale/actions/workflows/tests.yml/badge.svg)](https://github.com/wilfullyapt/ale/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/wilfullyapt/ale/branch/dev/graph/badge.svg)](https://codecov.io/gh/wilfullyapt/ale)
[![Python Versions](https://img.shields.io/pypi/pyversions/ale-cli.svg)](https://pypi.org/project/ale-cli/)

ALE is a command-line tool designed to run local files (`.py`, `.sh`) from a designated `.ale` directory. It provides a convenient way to organize and execute project-specific scripts and tools.

## Installation

You can install ALE using pip:

```bash
pip install ale-cli
```

Or using Poetry:

```bash
poetry add ale-cli
```

## Usage

1. Create a `.ale` directory in your project root:
```bash
mkdir .ale
```

2. Place your executable files in the `.ale` directory:
```bash
# Example structure
.ale/
  ├── setup.py      # Project setup script
  ├── cleanup.sh    # Cleanup script
  ├── test.py       # Test runner
  └── tools/        # Additional tools
```

3. Run files using the `ale` command:
```bash
# Basic usage
ale script_name [arg1 [arg2 ...]]

# Examples
ale setup.py --dev    # Run setup.py with --dev flag
ale cleanup.sh        # Run cleanup script
ale test.py -v       # Run tests with verbose flag

# Run Python scripts in interactive mode
ale -i script.py     # Opens Python REPL after script execution
```

## Features

- **Multiple File Types**: Runs Python scripts, shell scripts, and other executable files
- **Automatic Directory Detection**: Finds the `.ale` directory in your project
- **Argument Passing**: Seamlessly passes command line arguments to scripts
- **Interactive Mode**: Run Python scripts with a REPL (`-i` flag)
- **Error Handling**: Provides clear error messages and proper exit codes
- **Project Organization**: Keeps utility scripts organized in one place

## Project Structure

```
ale/
├── src/
│   └── ale/
│       ├── __init__.py
│       └── cli.py
├── tests/
│   └── test_cli.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Development

To set up the development environment:

1. Clone the repository:
```bash
git clone https://github.com/wilfullyapt/ale.git
cd ale
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
