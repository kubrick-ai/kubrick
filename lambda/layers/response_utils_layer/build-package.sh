#!/bin/bash
set -e

PACKAGE_NAME="package"

# Clean previous builds
rm -rf python ${PACKAGE_NAME}.zip ${PACKAGE_NAME}/ *.egg-info/ build/

# Create a temporary python directory for packaging the layer
mkdir python

# Install dependencies using uv with pyproject.toml for Linux/AMD64 Python 3.13
uv pip install --target python/ --python-platform x86_64-unknown-linux-gnu --python-version 3.13 .

# Copy Python source files to package directory
cp *.py python/

# Create a zip file containing everything from the package directory at the zip root
zip -r ${PACKAGE_NAME}.zip python/

# Clean up the temporary package directory
rm -rf python

echo "Lambda layer deployment package created: ${PACKAGE_NAME}.zip"
