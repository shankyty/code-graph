#!/bin/bash

# profile.sh - Profile Code Chunker using py-spy with native extensions
# Usage: ./profile.sh [options] <source_dir> --output <output_file>
# Options:
#   --profile-out <path>    Specify output file or directory for the flamegraph (default: profile.svg)

# Set PYTHONPATH to include the current directory
export PYTHONPATH=.

# Detect System Info for Efficiency Reporting (Shared with run.sh)
echo "--- Code Chunker Profiler ---"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CORES=$(nproc)
    if [ -f /sys/devices/virtual/dmi/id/product_name ]; then
        MODEL=$(cat /sys/devices/virtual/dmi/id/product_name)
    else
        MODEL="Linux Workstation"
    fi
    echo "Detected Linux System: $MODEL"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    CORES=$(sysctl -n hw.logicalcpu)
    MODEL=$(sysctl -n hw.model)
    echo "Detected macOS System: $MODEL"
else
    CORES=1
    echo "Detected Generic System"
fi

echo "Available CPU Cores: $CORES"
echo "--------------------------------"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for py-spy
if ! command_exists py-spy; then
    echo "py-spy not found. Attempting to install via pip..."
    if command_exists uv; then
        # Ensure venv exists for uv pip install
        if [ ! -d ".venv" ]; then
            echo "Creating virtual environment..."
            uv venv
        fi
        uv pip install py-spy
        # Add local venv bin to PATH
        export PATH="$(pwd)/.venv/bin:$PATH"
    else
        pip install py-spy
    fi

    # Check again
    if ! command_exists py-spy; then
        # Try to find it in local bin paths
        PATH=$PATH:$HOME/.local/bin
        if ! command_exists py-spy; then
             if [ -f ".venv/bin/py-spy" ]; then
                export PATH="$(pwd)/.venv/bin:$PATH"
             fi
        fi
    fi
fi

if ! command_exists py-spy; then
    echo "Error: py-spy is not installed and could not be installed automatically."
    echo "Please install py-spy manually."
    exit 1
fi

# Default output file
OUTPUT_PROFILE="profile.svg"
ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile-out)
            if [[ -d "$2" ]]; then
                OUTPUT_PROFILE="${2%/}/profile.svg"
            else
                OUTPUT_PROFILE="$2"
            fi
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

echo "Profiling to $OUTPUT_PROFILE..."

# Resolve python executable
if command_exists uv; then
    PYTHON_EXEC=$(uv run which python)
else
    PYTHON_EXEC=$(which python3 || which python)
fi
echo "Resolved Python: $PYTHON_EXEC"

# Run py-spy
# We pass --workers explicitly based on detection, but user args (ARGS) come last so they can override
py-spy record --native -o "$OUTPUT_PROFILE" -- "$PYTHON_EXEC" src/main.py --workers "$CORES" "${ARGS[@]}"
