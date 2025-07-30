variable "secrets_manager_name" {
  description = "The name of the AWS Secrets Manager secret containing API keys and RDS credentials"
  type        = string
  default     = "KubrickEmbeddingTaskConsumerSecret"
  # default     = "KubrickEmbeddingTaskConsumerSecret" ## Changed to try to make testing work, delete this
}