#!/bin/bash
set -e

PACKAGE_NAME="package"

# Clean previous builds
rm -rf package ${PACKAGE_NAME}.zip ${PACKAGE_NAME}/ *.egg-info/ build/

# Create a temporary directory for packaging
mkdir package

# Install dependencies using uv with pyproject.toml for Linux/AMD64 Python 3.13
uv pip install --target package/ --python-platform x86_64-unknown-linux-gnu --python-version 3.13 .

# Copy Python source files to package directory
cp *.py package/

# Copy schema SQL file to package directory
cp schema.sql package/

# Copy config JSON to package directory
cp config.json package/

# Create a zip file containing everything from the package directory at the zip root
cd package
zip -r ../${PACKAGE_NAME}.zip .
cd ..

# Clean up the temporary package directory
rm -rf package

echo "Lambda deployment package created: ${PACKAGE_NAME}.zip"
