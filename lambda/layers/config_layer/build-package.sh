#!/bin/bash
set -e

PACKAGE_NAME="package"

# Fixed timestamp for reproducible builds
FIXED_TIMESTAMP="202001010000"

# Clean previous builds
rm -rf python ${PACKAGE_NAME}.zip ${PACKAGE_NAME}/ *.egg-info/ build/

# Create a temporary python directory for packaging the layer
mkdir python

# Install dependencies using uv with pyproject.toml for Linux/AMD64 Python 3.13 using python3.13
uv pip install --target python/ --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --python python3.13 .

# Copy Python source files to package directory
cp *.py python/

# Remove common non-essential files
find python -type d -name "__pycache__" -exec rm -rf {} +
find python -type f -name "*.pyc" -delete
find python -type f -name "*.DS_Store" -delete

# Set consistent timestamps for all files
find python -exec touch -h -t ${FIXED_TIMESTAMP} {} +

# Create a zip file containing everything from the package directory at the zip root
find python -type f | LC_ALL=C sort | zip -X -@ ${PACKAGE_NAME}.zip

# Clean up the temporary package directory
rm -rf python

echo "Lambda layer deployment package created: ${PACKAGE_NAME}.zip"
