#!/bin/bash
set -e

echo "Building all Lambda packages..."

# Get the absolute path of the script's directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Find all directories with pyproject.toml files in the lambda directory
for dir in $(find lambda -name "pyproject.toml" -exec dirname {} \;); do
  echo "Building package in: $dir"
  cd "$dir"

  # Run the build script
  bash "$SCRIPT_DIR/lambda/build-package.sh"

  # Return to the root directory
  cd - >/dev/null

  echo "✓ Completed building: $dir"
done

echo "All Lambda packages built successfully!"
