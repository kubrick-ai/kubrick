variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket that Lambda functions will access"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "secret_arn" {
  description = "ARN of the Secrets Manager secret to allow access to"
  type        = string
}

variable "embedding_task_queue_arn" {
  description = "ARN of the SQS queue for sending messages"
  type        = string
}