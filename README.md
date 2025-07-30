# Kubrick

## Terraform Installation Guide

The Kubrick Terraform directory provides everything you need to set up Kubrick
in a production environment. Using Terraform, you can deploy the required AWS
infrastructure, which include: Lambdas, API Gateway, CloudFront, S3, SQS, and
RDS. This guide will walk you throw provisioning Kubrick's architecture using
Terraform.

### Getting Started

To deploy Kubrick in your AWS account, follow these steps:

1. Install Prerequisites:

- [Install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#getting-started-install-instructions)

2. Clone the Repository:

```
cd clone https://github.com/kubrick-ai/kubrick.git
cd kubrick/terraform
```

### Setting Up Secrets

Kubrick uses AWS Secrets Manager to securely store sensitive information like
database credentials and your TwelveLabs API key.

1. **Create Credentials**: Run the following command to create a secret for your
   PostgreSQL database credentials and TwelveLabs API key. Replace the values as
   necessary:

```
aws secretsmanager create-secret \
    --region <aws_region> \
    --name "kubrick_secret" \
    --description "Secret store for Kubrick application" \
    --secret-string '{
        "DB_USERNAME": <db_username>,
        "DB_PASSWORD": <db_password>
        "TWELVELABS_API_KEY": <twelvelabs_API_key>
    }'
```

- `<aws_region>` : Replace with your AWS region (e.g., `us-east-2`)
- `db_username` : Replace with your PostgreSQL username (e.g., `postgres`).
- `db_password` : Replace with your PostgreSQL password.
- `twelvelabs_API_key`: Replace with your TwelveLabs API key.

### Deploying Kubrick

1. **Initialize Terraform**: Run the following command to set your AWS region
   and provision the architecture: `terraform init`

2. **Apply the Terraform Configuration**: Run the following command to set your
   AWS region and provision the architecture:

// TODO

