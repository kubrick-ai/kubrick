variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-2"
}

variable "secrets_manager_name" {
  description = "The name of the AWS Secrets Manager secret containing API keys and RDS credentials"
  type        = string
  default     = "kubrick_secrets"
  # default     = "KubrickEmbeddingTaskConsumerSecret" ## Changed to try to make testing work, delete this
}

