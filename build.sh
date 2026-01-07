#!/bin/bash
# Build script for Render deployment
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Build completed successfully!"
