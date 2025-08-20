# Kubrick

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [CLI Tool](#cli-tool)
- [Deploying Kubrick](#deploying-kubrick)
- [Working with Existing Secrets](#working-with-existing-secrets)
- [Troubleshooting](#troubleshooting)
- [Cleanup and Management](#cleanup-and-management)
- [Advanced Configurations](#advanced-configurations)
- [IaC File Structure](#iac-file-structure)

## Overview

The Kubrick Terraform directory provides everything you need to set up Kubrick
in a production environment. Using Terraform, you can deploy the required AWS
infrastructure, which includes: Lambdas, API Gateway, CloudFront, S3, SQS, and
RDS. This guide will walk you through provisioning Kubrick's architecture using
Terraform.

## Architecture

Kubrick deploys a complete serverless architecture on AWS with the following
components:

- **AWS Lambda** - Serverless compute for video processing and API logic
- **API Gateway** - REST API endpoints and request routing for frontend
  communication
- **CloudFront** - Content delivery network for fast global asset delivery
- **S3 Buckets** - Object storage for video uploads and static content
- **SQS Queues** - Message queuing for asynchronous video processing workflows
- **RDS PostgreSQL** - Managed database for persistent application data
- **Secrets Manager** - Encrypted storage for database credentials and API keys
- **IAM Roles & Policies** - Security permissions and access control for all
  services

## Prerequisites

Before deploying Kubrick, ensure you have the following:

### Required Software

- **Terraform** (>= 1.0) -
  [Installation Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- **AWS CLI** (>= 2.15.0) -
  [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#getting-started-install-instructions)
- **Python** (>= 3.13) - [Installation Guide](https://www.python.org/downloads/)
- **uv** -
  [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js** (>= 24.2.0) & **npm** (>= 11.4.2) -
  [Installation Guide](https://nodejs.org/)

### AWS Account Requirements

- **AWS Account** with appropriate permissions
- **AWS CLI configured** with credentials (`aws configure`)
- **TwelveLabs API Key** -
  [Get your API key](https://docs.twelvelabs.io/docs/api-key)

### Required AWS Permissions

Your AWS user/role needs the following permissions to deploy Kubrick:

- `AmazonS3FullAccess`
- `AWSLambda_FullAccess`
- `AmazonAPIGatewayAdministrator`
- `CloudFrontFullAccess`
- `AmazonSQSFullAccess`
- `AmazonRDSFullAccess`
- `SecretsManagerReadWrite`
- `IAMFullAccess`

> **Note**: For production deployments, consider using more restrictive custom
> policies following the principle of least privilege.

## Getting Started

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/kubrick-ai/kubrick.git
   ```

## CLI Tool

Kubrick includes a command-line interface tool that simplifies deployment and
management. The CLI provides interactive prompts and handles Terraform
operations automatically.

### Installation

1. **Navigate to CLI directory:**

   ```bash
   cd kubrick/cli
   ```

2. **Build the CLI:**

   ```bash
   npm run build
   ```

### CLI Commands

- `kubrick deploy` - Deploy new or existing Kubrick infrastructure with
  interactive prompts
- `kubrick destroy` - Destroy existing Kubrick infrastructure with interactive
  prompts
- `kubrick --help` - Show help message

### CLI Usage

The CLI provides an interactive experience for infrastructure management:

```bash
kubrick deploy    # Deploy with guided prompts
kubrick destroy   # Destroy with guided prompts
```

The CLI will prompt you for required configuration values and handle the
Terraform deployment process automatically.

## Deploying Kubrick

You can deploy Kubrick using either the CLI tool (recommended) or manual
Terraform commands.

### Option A: Using the CLI Tool (Recommended)

The easiest way to deploy Kubrick is using the CLI tool:

1. **Build and use the CLI** (see [CLI Tool](#cli-tool) section above)
2. **Run deployment:**

   ```bash
   kubrick deploy
   ```

3. **Follow the interactive prompts** to configure your deployment

### Option B: Manual Terraform Deployment

For advanced users who prefer direct Terraform control:

1. **Clone and Prepare Repository**:

```bash
git clone https://github.com/kubrick-ai/kubrick.git
cd kubrick
```

2. **Build Lambda Packages**:
  Build the serverless functions and layers manually with
  ```bash
  ./lambda/build-package.sh
  ```
  or use your own CI/CD solution.


3. **Initialize Terraform**:
  Navigate to the Terraform directory and initialize:
   ```bash
   cd kubrick/terraform
   terraform init
   ```

4. **Configure Variables**: Create a `terraform.tfvars` file with your
   configuration:

   ```hcl
   # Required variables
   aws_region = "us-east-1"  # Your AWS region

   # Database credentials
   db_username = "postgres"  # Your PostgreSQL username
   db_password = "your-password"  # Your PostgreSQL password

   # API keys
   twelvelabs_api_key = "your-twelvelabs-api-key"  # Your TwelveLabs API key

   # Optional: Override default values
   aws_profile = "default"
   secrets_manager_name = "kubrick_secret"
   ```

   If you don't create a `terraform.tfvars` file, Terraform will prompt you for
   these values during deployment.

5. **Review Deployment Plan**:

   Generate and review the execution plan:

   ```bash
   terraform plan
   ```

6. **Deploy Infrastructure**:

   Apply the Terraform configuration:

   ```bash
   terraform apply   # Deploy the infrastructure


## Working with Existing Secrets

If you already have a secret named `kubrick_secret` in AWS Secrets Manager,
you'll need to import it into Terraform's state:

1. **Verify Secret Contents**: Ensure your existing secret contains the required
   keys:

   ```bash
   aws secretsmanager get-secret-value \
    --secret-id kubrick_secret \
    --query SecretString --output text
   ```

   Required keys:
   - `DB_USERNAME`
   - `DB_PASSWORD`
   - `TWELVELABS_API_KEY`

   If your secret is missing any keys or has different key names, update it
   before importing.

2. **Update Secret if Needed**:
   If keys are missing or have different names:

   ```bash
   aws secretsmanager update-secret \
   --secret-id kubrick_secret \
   --secret-string '{
     "DB_USERNAME": "postgres",
     "DB_PASSWORD": "your-password",
     "TWELVELABS_API_KEY": "your-api-key"
   }'
   ```
3. **Import Existing Secret**:

   Import the secret into Terraform state:

   ```bash
   terraform import module.secrets_manager.aws_secretsmanager_secret.kubrick_secret kubrick_secret
   ```

4. **Verify Import**:

   ```bash
   terraform plan
   ```
### Handling Resource Conflicts

   Common Import Issues

   - ResourceExistsException: Follow the secret import steps above
   - VPC/Subnet conflicts: Ensure your AWS account doesn't have conflicting default VPC settings
   - IAM role conflicts: Check for existing roles with similar names

<!-- - **ResourceExistsException**: If you get an error that the secret already
  exists, follow the "Working with Existing Secrets" section above to import it. -->

### Terraform Architecture Overview

#### Core Modules

- `api_gateway` - REST API endpoints for video operations
- `cloudfront` - CDN for global content delivery
- `dynamodb` - Embedding cache for performance optimization
- `iam` - Roles and policies for service permissions
- `lambda` - Serverless functions and layers
- `rds` - PostgreSQL database for metadata
- `s3` - Storage buckets for videos and static assets
- `s3_notifications` - Event triggers for video processing
- `secrets_manager` - Secure credential storage
- `sqs` - Message queues for async processing
- `vpc_network` - Network infrastructure and security

#### Lambda Functions Deployed

- API Handlers:

   - `api_fetch_tasks_handler` - Task status and management
   - `api_fetch_videos_handler` - Video listing and metadata
   - `api_search_handler` - Semantic search with embeddings
   - `api_video_upload_link_handler` - Presigned upload URLs

- Processing Functions:
   - `db_bootstrap` - Database initialization
   - `s3_delete_handler` - Cleanup on video deletion
   - `sqs_embedding_task_consumer` - Process embedding jobs
   - `sqs_embedding_task_producer` - Create embedding jobs

- Shared Layers: 
   - `config_layer` - Common configuration utilities
   - `embed_service_layer` - TwelveLabs API integration
   - `response_utils_layer` - HTTP response formatting
   - `s3_utils_layer` - S3 operation utilities
   - `vector_database_layer` - Vector similarity operations

### Verification and Testing

   After deployment completes:

   1. **Check Terraform Output**:
      Review important outputs:

      ```bash
      terraform output
      ```

      Key outputs include:

      - CloudFront distribution URL
      - API Gateway endpoint
      - S3 bucket names
      - RDS endpoint
   
   2. **Verify AWS Resources**:

      Check resource creation:

      ```bash
      # Lambda functions
      aws lambda list-functions --query 'Functions[?contains(FunctionName, `kubrick`)]'

      # API Gateway
      aws apigateway get-rest-apis --query 'items[?contains(name, `kubrick`)]'

      # S3 buckets
      aws s3 ls | grep kubrick
      ```
   
   3. **Test the Playground**:

      Access the CloudFront URL from the Terraform output to test the web interface.
   
   4. **API Health Check**:

      Test API endpoints:

      ```bash
      curl https://your-api-gateway-url/v1_0/videos
      ```

### Customization Options

#### Custom AWS Region

   Update aws_region in your `terraform.tfvars`:

   ```bash
   aws_region = "eu-west-1"  # Europe (Ireland)
   ```

#### Custom Database Configuration
   Modify database settings in terraform.tfvars:

   ```bash
   db_username = "kubrick_admin"
   db_password = "your-complex-password-here"
   ```

#### API Gateway Stage Names

   Change the API version/stage:

   ```bash
   stage_name = "production"  # Creates /production/ endpoints
   ```

## Troubleshooting

### Common Issues

- Build script errors: Ensure Python 3.13 and `uv` are installed
- Terraform init fails: Check AWS credentials and region
- Lambda package too large: Verify dependencies in `pyproject.toml` files
- RDS timeout: Increase default timeout or check VPC configuration

### State Management

```bash
# Backup state
terraform state pull > kubrick.tfstate.backup

# List resources in state
terraform state list

# Remove problematic resource
terraform state rm aws_s3_bucket.example
```

## Cleanup and Management

### Destroying Infrastructure

```bash
terraform destroy
```
***This will permanently delete all data including uploaded videos and database contents.***

### Selective Resource Management

Remove specific resources:

```bash
# Remove CloudFront
terraform destroy -target=module.cloudfront

# Remove RDS
terraform destroy -target=module.rds
```

## Advanced Configuration

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy Kubrick
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      - name: Terraform Deploy
        run: |
          cd terraform
          terraform init
          terraform apply -auto-approve
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          TF_VAR_twelvelabs_api_key: ${{ secrets.TWELVELABS_API_KEY }}
```

### Multi-Environment Setup

Create separate `.tfvars` files for each environment:

```bash
# Development
terraform apply -var-file="dev.tfvars"

# Production
terraform apply -var-file="prod.tfvars"
```

## IaC File Structure

```
kubrick/
├── ...
└── terraform/
    ├── modules/
    │   ├── api_gateway/
    │   ├── cloudfront/
    │   ├── dynamodb/
    │   ├── iam/
    │   ├── lambda/
    │   ├── rds/
    │   ├── s3/
    │   ├── s3_notifications/
    │   ├── secrets_manager/
    │   ├── sqs/
    │   └── vpc_network/
    ├── main.tf
    ├── variables.tf
    └── terraform.tfvars.example
```
