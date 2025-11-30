#!/bin/bash
# Quick script to run tests on Modal

echo "🚀 Deploying tests to Modal..."
echo ""

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI not found. Install it with: pip install modal"
    exit 1
fi

# Check if authenticated
if ! modal token list &> /dev/null; then
    echo "⚠️  Not authenticated with Modal. Run: modal token new"
    exit 1
fi

# Run the tests
echo "Running: modal run modal_test_deploy.py"
echo ""
modal run modal_test_deploy.py "$@"

