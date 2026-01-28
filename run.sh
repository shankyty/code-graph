#!/bin/bash

# run.sh - Efficiently run Code Chunker on workstations using uv

# Set PYTHONPATH to include the current directory
export PYTHONPATH=.

# Detect System Info for Efficiency Reporting
echo "--- Code Chunker Environment ---"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CORES=$(nproc)
    # Try to get product name, might require sudo or not exist on all systems, keeping it simple
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
echo "Code Chunker will automatically optimize worker count for this system."
echo "--------------------------------"

# Run the tool using uv
# uv automatically manages the virtual environment and dependencies
# We pass --workers explicitly based on our detection, but allow user to override (last arg wins)
uv run python src/main.py --workers "$CORES" "$@"
