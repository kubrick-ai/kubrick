variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket that Lambda functions will access"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}
