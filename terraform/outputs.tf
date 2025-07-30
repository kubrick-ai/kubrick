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

# API Gateway Outputs
output "api_gateway_id" {
  description = "The ID of the API Gateway REST API"
  value       = module.api_gateway.api_gateway_id
}

output "api_gateway_invoke_url" {
  description = "The invoke URL for the API Gateway deployment"
  value       = module.api_gateway.api_gateway_invoke_url
}

output "api_gateway_stage_name" {
  description = "The name of the API Gateway stage"
  value       = module.api_gateway.api_gateway_stage_name
}

output "videos_endpoint_url" {
  description = "Full URL for the videos endpoint"
  value       = module.api_gateway.videos_endpoint_url
}

output "search_endpoint_url" {
  description = "Full URL for the search endpoint"
  value       = module.api_gateway.search_endpoint_url
}

output "generate_upload_link_endpoint_url" {
  description = "Full URL for the generate-upload-link endpoint"
  value       = module.api_gateway.generate_upload_link_endpoint_url
}

output "tasks_endpoint_url" {
  description = "Full URL for the tasks endpoint"
  value       = module.api_gateway.tasks_endpoint_url
}

output "api_gateway_execution_arn" {
  description = "The execution ARN of the API Gateway REST API"
  value       = module.api_gateway.api_gateway_execution_arn
}

output "api_gateway_arn" {
  description = "The ARN of the API Gateway REST API"
  value       = module.api_gateway.api_gateway_arn
}
