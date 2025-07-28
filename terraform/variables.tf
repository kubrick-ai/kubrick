variable "secrets_manager_name" {
  description = "The name of the AWS Secrets Manager secret containing API keys and RDS credentials"
  type        = string
  default     = "kubrick_secrets"
}