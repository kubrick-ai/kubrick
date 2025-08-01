#!/bin/bash
set -e

# Global variables
AWS_PROFILE=""
AWS_REGION=""
SKIP_AUTH_CHECK=false

# Get the absolute path of the script's directory (root directory of project)
ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

show_help() {
  cat <<EOF
Usage: $0 [OPTIONS]

Deploy Kubrick infrastructure with Lambda packages and Terraform.

Options:
  --profile PROFILE    AWS CLI profile to use
  --region REGION      AWS region to deploy to
  --skip-auth-check    Skip AWS authentication validation
  --help              Show this help message

Examples:
  $0                           # Use default AWS profile and region
  $0 --profile production      # Use specific AWS profile
  $0 --region us-west-2        # Use specific AWS region
  $0 --skip-auth-check         # Skip AWS credential validation

EOF
}

parse_arguments() {
  while [[ $# -gt 0 ]]; do
    case $1 in
    --profile)
      AWS_PROFILE="$2"
      shift 2
      ;;
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --skip-auth-check)
      SKIP_AUTH_CHECK=true
      shift
      ;;
    --help | -h)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
    esac
  done
}

validate_aws_credentials() {
  echo "🔐 Validating AWS credentials..."

  # Set AWS profile if specified
  if [[ -n "$AWS_PROFILE" ]]; then
    export AWS_PROFILE="$AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
  fi

  # Set AWS region if specified
  if [[ -n "$AWS_REGION" ]]; then
    export AWS_DEFAULT_REGION="$AWS_REGION"
    echo "Using AWS region: $AWS_REGION"
  fi

  # Test AWS credentials
  if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS credentials not configured or invalid"
    echo "Please run 'aws configure' or set up your AWS credentials"
    if [[ -n "$AWS_PROFILE" ]]; then
      echo "Make sure the profile '$AWS_PROFILE' exists and is properly configured"
    fi
    exit 1
  fi

  # Get and display current AWS identity
  local identity
  identity=$(aws sts get-caller-identity 2>/dev/null)
  local account_id user_arn
  account_id=$(echo "$identity" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4)
  user_arn=$(echo "$identity" | grep -o '"Arn": "[^"]*"' | cut -d'"' -f4)

  echo "✅ AWS credentials validated"
  echo "Account ID: $account_id"
  echo "Identity: $user_arn"

  # Validate region is accessible
  if [[ -n "$AWS_REGION" ]]; then
    if ! aws ec2 describe-regions --region "$AWS_REGION" &>/dev/null; then
      echo "❌ Cannot access AWS region: $AWS_REGION"
      echo "Please check if the region exists and you have access to it"
      exit 1
    fi
    echo "✅ AWS region validated: $AWS_REGION"
  fi
}

check_aws_permissions() {
  echo "🔍 Checking AWS permissions..."

  local failed_checks=()

  # Test S3 access
  if ! aws s3 ls &>/dev/null; then
    failed_checks+=("S3")
  fi

  # Test Lambda access
  if ! aws lambda list-functions --max-items 1 &>/dev/null; then
    failed_checks+=("Lambda")
  fi

  # Test IAM access
  if ! aws iam list-roles --max-items 1 &>/dev/null; then
    failed_checks+=("IAM")
  fi

  # Test API Gateway access
  if ! aws apigateway get-rest-apis --limit 1 &>/dev/null; then
    failed_checks+=("API Gateway")
  fi

  if [[ ${#failed_checks[@]} -gt 0 ]]; then
    echo "⚠️  Warning: Missing permissions for: ${failed_checks[*]}"
    echo "The deployment may fail. Consider reviewing your AWS permissions."
    echo "Required permissions are listed in README.md"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "❌ Deployment cancelled by user"
      exit 1
    fi
  else
    echo "✅ AWS permissions validated"
  fi
}

check_dependencies() {
  echo "🔍 Checking dependencies..."

  local missing_deps=()

  # Check for required tools
  if ! command_exists terraform; then
    missing_deps+=("terraform")
  fi

  if ! command_exists aws; then
    missing_deps+=("aws-cli")
  fi

  if ! command_exists python3; then
    missing_deps+=("python3")
  fi

  if ! command_exists uv; then
    missing_deps+=("uv")
  fi

  if [ ${#missing_deps[@]} -ne 0 ]; then
    echo "❌ Missing required dependencies: ${missing_deps[*]}"
    echo "Please install the missing dependencies and try again."
    echo "See README.md for installation instructions."
    exit 1
  fi

  echo "✅ All dependencies are installed"

  # Validate AWS credentials unless skipped
  if [[ "$SKIP_AUTH_CHECK" != "true" ]]; then
    validate_aws_credentials
    check_aws_permissions
  else
    echo "⚠️  Skipping AWS authentication check"
  fi
}

build_lambdas() {
  echo "🏗️  Building Lambda packages..."

  if [ ! -f "$ROOT_DIR/build-lambda-packages.sh" ]; then
    echo "❌ build-lambda-packages.sh not found"
    exit 1
  fi

  bash "$ROOT_DIR/build-lambda-packages.sh"
  echo "✅ Lambda packages built successfully"
}

deploy_terraform() {
  echo "🏗️  Deploying infrastructure with Terraform..."

  cd "$ROOT_DIR/terraform"

  # Check if terraform directory exists
  if [ ! -d "$ROOT_DIR/terraform" ]; then
    echo "❌ Terraform directory not found"
    exit 1
  fi

  # Initialize Terraform if not already initialized
  if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
  fi

  # Plan the deployment
  echo "📋 Planning Terraform deployment..."
  terraform plan

  # Ask for confirmation before applying
  echo ""
  read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
  echo ""

  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Applying Terraform configuration..."
    terraform apply
    echo "✅ Infrastructure deployed successfully!"
  else
    echo "❌ Deployment cancelled by user"
    exit 1
  fi

  # Return to script directory
  cd "$ROOT_DIR"
}

main() {
  echo "🚀 Starting Kubrick deployment..."

  parse_arguments "$@"
  check_dependencies
  build_lambdas
  deploy_terraform

  echo ""
  echo "🎉 Kubrick deployment completed successfully!"
  echo "Check the Terraform outputs for important resource information."
}

# Execute main function
main "$@"
