#!/bin/bash
set -e

# Determine if this is a layer (has python/) or function (has package/)
if [ -f "pyproject.toml" ]; then
  # Check if we're in a layer directory
  if [[ $(pwd) == *"/layers/"* ]]; then
    TARGET_DIR="package/python"
  else
    TARGET_DIR="package"
  fi
else
  echo "No pyproject.toml found"
  exit 1
fi

# Clean previous builds
rm -rf package *.egg-info/ build/

# Create target directory
mkdir -p ${TARGET_DIR}

# Install dependencies
uv pip install --target ${TARGET_DIR}/ --python-platform x86_64-unknown-linux-gnu --python-version 3.13 --python python3.13 .

# Copy source files
cp *.py ${TARGET_DIR}/
# Copy additional files if they exist
[ -f "schema.sql" ] && cp schema.sql ${TARGET_DIR}/

# Remove non-essential files
find ${TARGET_DIR} -type d -name "__pycache__" -exec rm -rf {} +
find ${TARGET_DIR} -type f -name "*.pyc" -delete
find ${TARGET_DIR} -type f -name "*.DS_Store" -delete

echo "Dependencies and source files installed in ${TARGET_DIR}/ directory"

