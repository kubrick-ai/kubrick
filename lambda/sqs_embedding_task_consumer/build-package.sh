#!/bin/bash
set -e

# Clean previous builds
rm -rf package.zip package/ *.egg-info/ build/

# Create a temporary directory for packaging
mkdir package

# Copy Python source files to package directory
cp lambda_function.py package/
cp config.py package/
cp config.json package/

# Install dependencies using uv with pyproject.toml for Linux/AMD64 Python 3.13
uv pip install --target package/ --python-platform x86_64-unknown-linux-gnu --python-version 3.13 .

# Create a zip file containing everything from the package directory at the zip root
zip -r package.zip -C package .

# Clean up the temporary package directory
rm -rf package

echo "Lambda deployment package created: ${PACKAGE_NAME}.zip"
