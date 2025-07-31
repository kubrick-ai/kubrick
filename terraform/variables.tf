variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-2"
}

variable "secrets_manager_name" {
  description = "The name of the AWS Secrets Manager secret containing API keys and RDS credentials"
  type        = string
  default     = "kubrick_secret"
}

variable "db_username" {
  description = "Database username for the Kubrick application"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password for the Kubrick application"
  type        = string
  sensitive   = true
}

variable "twelvelabs_api_key" {
  description = "TwelveLabs API key for the Kubrick application"
  type        = string
  sensitive   = true
}

variable "aws_profile" {
  description = "AWS CLI profile to use for local-exec provisioners"
  type        = string
  default     = "default"
}
