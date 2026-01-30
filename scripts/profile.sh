#!/bin/bash

# profile.sh - Profile Code Chunker using py-spy with native extensions

# Set PYTHONPATH to include the current directory
export PYTHONPATH=.

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for py-spy
if ! command_exists py-spy; then
    echo "py-spy not found. Attempting to install via pip..."
    if command_exists uv; then
        uv pip install py-spy
    else
        pip install py-spy
    fi

    # Check again
    if ! command_exists py-spy; then
        # Try to find it in local bin paths if pip installed it there
        PATH=$PATH:$HOME/.local/bin
        if ! command_exists py-spy; then
             # Try running as python module? No, py-spy is a binary.
             # Maybe it was installed in the venv?
             if [ -f ".venv/bin/py-spy" ]; then
                export PATH=$PATH:$(pwd)/.venv/bin
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

# Parse arguments: extract --profile-out, pass rest to main.py
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile-out)
            OUTPUT_PROFILE="$2"
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

echo "Profiling to $OUTPUT_PROFILE..."
echo "Running with arguments: ${ARGS[@]}"

# Resolve python executable to avoid uv wrapping issues with py-spy
if command_exists uv; then
    PYTHON_EXEC=$(uv run which python)
else
    PYTHON_EXEC=$(which python3 || which python)
fi
echo "Resolved Python: $PYTHON_EXEC"

py-spy record --native -o "$OUTPUT_PROFILE" -- "$PYTHON_EXEC" src/main.py "${ARGS[@]}"
