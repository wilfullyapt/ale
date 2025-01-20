# Access Local Execution (ALE)
ALE is a command-line tool designed to run local files (`.py`, `.sh`) from a designated `.ale` directory.

## Usage

1. Create a `.ale` directory in your project:
```bash
mkdir .ale
```

2. Place your executable files in the `.ale` directory.

3. Run files using the `ale` command:
```bash
ale script_name [arg1 [arg2 ...]]
```

## Features

- Runs Python scripts, shell scripts, and other executable files
- Automatically detects the `.ale` directory
- Passes through command line arguments to the executed script
- Provides helpful error messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.
