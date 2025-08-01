# Kubrick

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Deploying Kubrick](#deploying-kubrick)
- [Working with Existing Secrets](#working-with-existing-secrets)
- [Troubleshooting](#troubleshooting)

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

1. **Build lambda packages:**

   ```bash
   ./build-all-packages.sh
   ```

### Deploying Kubrick

The Kubrick deployment process is fully managed by Terraform. Follow these
steps:

1. **Initialize Terraform**:

   ```bash
   cd kubrick/terraform
   terraform init
   ```

2. **Configure Variables**: Create a `terraform.tfvars` file with your
   configuration:

   ```hcl
   # Required variables
   aws_region = "us-east-2"  # Your AWS region

   # Database credentials
   db_username = "postgres"  # Your PostgreSQL username
   db_password = "your-secure-password"  # Your PostgreSQL password

   # API keys
   twelvelabs_api_key = "your-twelvelabs-api-key"  # Your TwelveLabs API key

   # Optional: Override default values
   # secrets_manager_name = "kubrick_secret"
   # aws_profile = "default"
   ```

   If you don't create a `terraform.tfvars` file, Terraform will prompt you for
   these values during deployment.

3. **Deploy Infrastructure**:

   ```bash
   terraform plan    # Review planned changes
   terraform apply   # Deploy the infrastructure
   ```

### Working with Existing Secrets

If you already have a secret named `kubrick_secret` in AWS Secrets Manager,
you'll need to import it into Terraform's state:

1. **Verify Secret Contents**: Ensure your existing secret contains the required
   keys:

   ```bash
   aws secretsmanager get-secret-value --secret-id kubrick_secret --query SecretString --output text
   ```

   The secret should contain these keys:
   - `DB_USERNAME`
   - `DB_PASSWORD`
   - `TWELVELABS_API_KEY`

   If your secret is missing any keys or has different key names, update it
   before importing.

2. **Import Existing Secret**:

   ```bash
   terraform import module.secrets_manager.aws_secretsmanager_secret.kubrick_secret kubrick_secret
   ```

3. **Verify Import**:

   ```bash
   terraform plan  # Should show no changes if secret matches configuration
   ```

### Troubleshooting

- **ResourceExistsException**: If you get an error that the secret already
  exists, follow the "Working with Existing Secrets" section above to import it.
- **Missing Variables**: Terraform will prompt for any required variables not
  specified in `terraform.tfvars`.
