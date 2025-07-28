# S3 Bucket Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "s3_bucket_id" {
  description = "ID of the S3 bucket"
  value       = module.s3.bucket_id
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = module.s3.bucket_domain_name
}

# Lambda IAM Role Outputs
output "lambda_s3_readonly_role_arn" {
  description = "ARN of the Lambda S3 read-only IAM role"
  value       = module.iam.lambda_s3_readonly_role_arn
}

output "lambda_s3_readonly_role_name" {
  description = "Name of the Lambda S3 read-only IAM role"
  value       = module.iam.lambda_s3_readonly_role_name
}

output "lambda_s3_full_access_role_arn" {
  description = "ARN of the Lambda S3 full access IAM role"
  value       = module.iam.lambda_s3_full_access_role_arn
}

output "lambda_s3_full_access_role_name" {
  description = "Name of the Lambda S3 full access IAM role"
  value       = module.iam.lambda_s3_full_access_role_name
}

# IAM Policy Outputs
output "lambda_s3_readonly_policy_arn" {
  description = "ARN of the Lambda S3 read-only policy"
  value       = module.iam.lambda_s3_readonly_policy_arn
}

output "lambda_s3_full_access_policy_arn" {
  description = "ARN of the Lambda S3 full access policy"
  value       = module.iam.lambda_s3_full_access_policy_arn
}

# SQS Queue Outputs
output "sqs_queue_url" {
  description = "URL of the main SQS queue for embedding tasks"
  value       = module.sqs.queue_url
}

output "sqs_queue_arn" {
  description = "ARN of the main SQS queue for embedding tasks"
  value       = module.sqs.queue_arn
}

output "sqs_queue_name" {
  description = "Name of the main SQS queue for embedding tasks"
  value       = module.sqs.queue_name
}
