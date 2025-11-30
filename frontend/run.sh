#!/bin/bash
# Simple startup script for the LoRA Training UI

cd "$(dirname "$0")"

echo "🎨 Starting LoRA Training UI..."
echo ""

# Check if dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Make sure you're in the frontend directory."
    exit 1
fi

echo "✅ Starting server on http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

python3 app.py

