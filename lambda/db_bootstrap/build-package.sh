#!/bin/bash
set -e

PACKAGE_NAME="package"

# Fixed timestamp for reproducible builds
FIXED_TIMESTAMP="202001010000"

# Clean previous builds
rm -rf package ${PACKAGE_NAME}.zip ${PACKAGE_NAME}/ *.egg-info/ build/

# Create a temporary directory for packaging
mkdir package

# Install dependencies using uv with pyproject.toml for Linux/AMD64 Python 3.13 using python3.13
uv pip install --target package/ --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --python python3.13 .

# Copy source files to package directory
cp *.py package/
cp schema.sql package/

# Remove common non-essential files
find package -type d -name "__pycache__" -exec rm -rf {} +
find package -type f -name "*.pyc" -delete
find package -type f -name "*.DS_Store" -delete

# Set consistent timestamps for all files
find package -exec touch -h -t ${FIXED_TIMESTAMP} {} +

# Create a zip file containing everything from the package directory at the zip root
cd package
find . -type f | LC_ALL=C sort | zip -X -@ ../${PACKAGE_NAME}.zip
cd ..

# Clean up the temporary package directory
rm -rf package

echo "Lambda deployment package created: ${PACKAGE_NAME}.zip"
