#!/bin/bash

# Setup script for CustomGANStego Project
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "=== CustomGANStego Environment Setup ==="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Display Python version
PYTHON_VERSION=$(python3 --version)
echo "✓ Found $PYTHON_VERSION"
echo ""

# Create virtual environment
if [ -d "prjvenv" ]; then
    echo "⚠️  Virtual environment 'prjvenv' already exists."
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf prjvenv
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d "prjvenv" ]; then
    echo "Creating virtual environment 'prjvenv'..."
    python3 -m venv prjvenv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source prjvenv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo ""
    echo "✓ All dependencies installed successfully"
else
    echo "❌ Error: requirements.txt not found"
    exit 1
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To activate the virtual environment, run:"
echo "  source prjvenv/bin/activate"
echo ""
echo "To deactivate when you're done, run:"
echo "  deactivate"
echo ""
