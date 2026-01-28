# Code Chunker

A scalable tool to parse and chunk Java code, specifically designed for large monorepos. It resolves dependencies (Maven, Bazel) and extracts metadata for efficient processing.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (Fast Python package installer and resolver)
- Python 3.9+

## Installation

1.  Clone the repository.
2.  Ensure `uv` is installed.

    ```bash
    # On macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Usage

You can run the tool using the provided helper script `run.sh`, which automatically detects your system configuration and optimizes the execution. `uv` will automatically manage the Python environment and dependencies.

```bash
./run.sh <source_dir> --output <output_file> [options]
```

### Arguments

- `source_dir`: The root directory to scan for Java files.
- `--output`, `-o`: The path to the output file (required).
- `--format`, `-f`: Output format, either `json` (default) or `text`.
- `--workers`, `-w`: Number of worker processes. Defaults to the number of CPU cores.

### Examples

**Basic Usage:**

```bash
./run.sh /path/to/java/project --output output.json
```

**Specifying Output Format:**

```bash
./run.sh /path/to/java/project -o output.txt -f text
```

## Performance

The tool is optimized for high-performance workstations, such as:

-   **HP Z4 G4 Workstation** (utilizing all available cores/threads)
-   **MacBook Pro** (Apple Silicon M2/M3 Max)

The `run.sh` script automatically detects available resources to ensure efficient processing on these powerful machines.
