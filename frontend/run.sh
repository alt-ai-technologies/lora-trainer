#!/bin/bash
# Simple startup script for the LoRA Training UI

cd "$(dirname "$0")"

echo "🎨 Starting LoRA Training UI..."
echo ""

# Use system Python (not venv)
PYTHON_CMD="/usr/bin/python3"

# Check if system Python exists
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

# Check if dependencies are installed
if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing dependencies..."
    $PYTHON_CMD -m pip install --user flask flask-cors pyyaml --break-system-packages
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Make sure you're in the frontend directory."
    exit 1
fi

# Verify Flask is available
if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "❌ Error: Flask is not available. Please install dependencies first:"
    echo "   $PYTHON_CMD -m pip install --user flask flask-cors pyyaml --break-system-packages"
    exit 1
fi

echo "✅ Starting server on http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

$PYTHON_CMD app.py

