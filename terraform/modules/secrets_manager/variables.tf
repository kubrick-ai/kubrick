variable "name" {
  description = "The name of the AWS Secrets Manager secret"
  type        = string
  default     = "kubrick_app_secret"
}

variable "description" {
  description = "Description for the AWS Secrets Manager secret"
  type        = string
  default     = "Secret store for Kubrick application"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "db_username" {
  description = "Database username to store in the secret"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password to store in the secret"
  type        = string
  sensitive   = true
}

variable "twelvelabs_api_key" {
  description = "TwelveLabs API key to store in the secret"
  type        = string
  sensitive   = true
}
