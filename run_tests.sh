#!/bin/bash
# Script to run tests for the radio transcription project

echo "Running tests for radio transcription project..."
echo ""

# Run pytest with coverage
python -m pytest tests/ \
    --verbose \
    --cov=src \
    --cov-report=term \
    --cov-report=html \
    "$@"

echo ""
echo "Test run complete!"
echo "Coverage report saved to htmlcov/index.html"
