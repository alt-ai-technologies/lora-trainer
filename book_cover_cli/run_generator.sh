#!/bin/bash
# Wrapper script to ensure the CLI runs with the correct virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Activate virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✓ Using virtual environment: $VENV_PATH"
else
    echo "⚠️  Warning: Virtual environment not found at $VENV_PATH"
    echo "   Continuing with system Python..."
fi

# Run the generator
cd "$SCRIPT_DIR"
exec python3 book_cover_generator.py "$@"

