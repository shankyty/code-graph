# Code Chunker

A scalable tool to parse and chunk Java code, specifically designed for large monorepos. It resolves dependencies (Maven, Bazel) and extracts metadata for efficient processing.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (Fast Python package installer and resolver)
- [fzf](https://github.com/junegunn/fzf) (Command-line fuzzy finder, required for search feature)
- Python 3.9+

## Installation

1.  Clone the repository.
2.  Ensure `uv` and `fzf` are installed.

    ```bash
    # On macOS
    brew install fzf

    # On Linux (Ubuntu)
    sudo apt-get install fzf

    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Usage

You can run the tool using the provided helper script `run.sh`, which automatically detects your system configuration and optimizes the execution. `uv` will automatically manage the Python environment and dependencies.

```bash
./run.sh <source_dir> --output <output_file> [options]
```

### Interactive TUI

The tool runs with a **Rich-based Text User Interface (TUI)** that displays:
- Overall progress.
- Real-time status of each worker process.

**Search Feature:**
During execution, you can press **`s`** (followed by Enter if buffering occurs) to pause the progress view and open a **fuzzy search** (via `fzf`) to filter and view the status of all files (Pending, Processing, Done).

### Arguments

- `source_dir`: The root directory to scan for Java files.
- `--output`, `-o`: The path to the output file (required).
- `--format`, `-f`: Output format, either `json` (default) or `text`.
- `--workers`, `-w`: Number of worker processes. Defaults to the number of CPU cores.
- `--no-tui`: Disable the TUI and run in "Job Mode" with simple logging (useful for CI/CD or non-interactive environments).

### Examples

**Basic Usage:**

```bash
./run.sh /path/to/java/project --output output.json
```

**Job Mode (CI/CD):**

```bash
./run.sh /path/to/java/project -o output.json --no-tui
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

## Profiling

To analyze the performance of the tool and identify bottlenecks, you can use the `profile.sh` script. This script wraps `py-spy` to generate a flamegraph of the execution.

It accepts the same arguments as `run.sh`, with an optional `--profile-out` argument to specify the location of the flamegraph.

**Basic Profiling:**

```bash
./profile.sh /path/to/java/project --output output.json
```

This will generate a `profile.svg` file in the current directory.

**Specifying Profile Output:**

```bash
./profile.sh --profile-out /tmp/my_profile.svg /path/to/java/project --output output.json
```

You can also pass a directory to `--profile-out` (the file will be named `profile.svg` inside that directory):

```bash
./profile.sh --profile-out /tmp/profiles/ /path/to/java/project --output output.json
```

The script automatically detects your system configuration (OS, CPU cores) just like `run.sh` and handles the installation of `py-spy` if needed.
