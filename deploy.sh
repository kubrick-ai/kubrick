#!/bin/bash
set -e

# Global variables
AWS_PROFILE=""
AWS_REGION=""
SKIP_AUTH_CHECK=false

# Get the absolute path of the script's directory (root directory of project)
ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

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
      echo -e "${RED}Unknown option: $1${NC}"
      show_help
      exit 1
      ;;
    esac
  done
}

validate_aws_credentials() {
  echo -e "🔐 Validating AWS credentials..."

  # Set AWS profile if specified
  if [[ -n "$AWS_PROFILE" ]]; then
    export AWS_PROFILE="$AWS_PROFILE"
    echo -e "Using AWS profile: ${GREEN}$AWS_PROFILE${NC}"
  fi

  # Set AWS region if specified
  if [[ -n "$AWS_REGION" ]]; then
    export AWS_DEFAULT_REGION="$AWS_REGION"
    echo -e "Using AWS region: ${GREEN}$AWS_REGION${NC}"
  fi

  # Test AWS credentials
  if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS credentials not configured or invalid${NC}"
    echo "Please run 'aws configure' or set up your AWS credentials"
    if [[ -n "$AWS_PROFILE" ]]; then
      echo "Make sure the profile '$AWS_PROFILE' exists and is properly configured"
    fi
    exit 1
  fi

  # Get and display current AWS identity
  local account_id user_arn
  account_id=$(aws sts get-caller-identity --query "Account" --output text 2>/dev/null)
  user_arn=$(aws sts get-caller-identity --query "Arn" --output text 2>/dev/null)

  echo -e "${GREEN}✅ AWS credentials validated${NC}"
  echo "Account ID: $account_id"
  echo "Identity: $user_arn"

  # Validate region is accessible
  if [[ -n "$AWS_REGION" ]]; then
    if ! aws ec2 describe-regions --region "$AWS_REGION" &>/dev/null; then
      echo -e "${RED}❌ Cannot access AWS region: $AWS_REGION${NC}"
      echo "Please check if the region exists and you have access to it"
      exit 1
    fi
    echo -e "${GREEN}✅ AWS region validated: $AWS_REGION${NC}"
  fi
}

check_aws_permissions() {
  echo -e "🔍 Checking AWS permissions..."

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
    echo -e "${YELLOW}⚠️  Warning: Missing permissions for: ${failed_checks[*]}${NC}"
    echo "The deployment may fail. Consider reviewing your AWS permissions."
    echo "Required permissions are listed in README.md"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}❌ Deployment cancelled by user${NC}"
      exit 1
    fi
  else
    echo -e "${GREEN}✅ AWS permissions validated${NC}"
  fi
}

check_terraform_vars() {
  echo "📝 Checking Terraform variables..."

  local tfvars_file="$ROOT_DIR/terraform/terraform.tfvars"
  local tfvars_example="$ROOT_DIR/terraform/terraform.tfvars.example"

  if [[ ! -f "$tfvars_file" ]]; then
    echo -e "${YELLOW}⚠️  terraform.tfvars not found${NC}"
    echo ""
    echo "Terraform will prompt you for required variables during deployment."
    echo "Note: Values entered will NOT be saved for future deployments."
    echo ""
    if [[ -f "$tfvars_example" ]]; then
      echo "💡 To avoid this, copy terraform.tfvars.example to terraform.tfvars and fill in your values:"
      echo "   cp terraform/terraform.tfvars.example terraform/terraform.tfvars"
    else
      echo "💡 To avoid this, create a terraform.tfvars file with your variable values."
    fi
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}❌ Deployment cancelled by user${NC}"
      exit 1
    fi
  else
    echo -e "${GREEN}✅ Found terraform.tfvars${NC}"
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
    echo -e "${RED}❌ Missing required dependencies: ${missing_deps[*]}${NC}"
    echo "Please install the missing dependencies and try again."
    echo "See README.md for installation instructions."
    exit 1
  fi

  echo -e "${GREEN}✅ All dependencies are installed${NC}"

  # Validate AWS credentials unless skipped
  if [[ "$SKIP_AUTH_CHECK" != "true" ]]; then
    validate_aws_credentials
    check_aws_permissions
  else
    echo -e "${YELLOW}⚠️  Skipping AWS authentication check${NC}"
  fi
}

build_lambdas() {
  echo "🏗️  Building Lambda packages..."

  if [ ! -f "$ROOT_DIR/build-lambda-packages.sh" ]; then
    echo -e "${RED}❌ build-lambda-packages.sh not found${NC}"
    exit 1
  fi

  bash "$ROOT_DIR/build-lambda-packages.sh"
  echo -e "${GREEN}✅ Lambda packages built successfully${NC}"
}

deploy_terraform() {
  echo "🏗️  Deploying infrastructure with Terraform..."

  cd "$ROOT_DIR/terraform"

  # Check if terraform directory exists
  if [ ! -d "$ROOT_DIR/terraform" ]; then
    echo -e "${RED}❌ Terraform directory not found${NC}"
    exit 1
  fi

  # Check and collect Terraform variables
  check_terraform_vars

  # Initialize Terraform if not already initialized
  if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
  fi

  echo "🚀 Deploying Terraform configuration..."
  terraform apply
  echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"

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
  echo -e "${GREEN}🎉 Kubrick deployment completed successfully!${NC}"
  echo "Check the Terraform outputs for important resource information."
}

# Execute main function
main "$@"
