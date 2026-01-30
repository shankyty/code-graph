# Scripts

This directory contains utility scripts for Code Chunker.

## `profile.sh`

A wrapper script to profile the Code Chunker application using [py-spy](https://github.com/benfred/py-spy). It generates a flame graph of the execution, including native stack traces (e.g., from C extensions like `tree-sitter`).

### Prerequisites

- `py-spy`: The script will attempt to install it via `pip` or `uv` if not found.
- Linux or macOS (for native profiling support).

### Usage

The arguments are passed directly to `src/main.py`.

```bash
# Basic usage
./scripts/profile.sh <source_dir> -o <output_file> --no-tui

# Customizing profile output file (default: profile.svg)
./scripts/profile.sh <source_dir> -o <output_file> --no-tui --profile-out my_profile.svg
```

### Output

The script generates an SVG flame graph (default `profile.svg`) which can be opened in any web browser to interactively explore the performance hotspots.
