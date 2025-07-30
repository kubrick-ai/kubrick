#
output "db_bootstrap_role_arn" {
  description = "IAM role ARN for database bootstrap Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_db_bootstrap"].arn
}

output "s3_delete_handler_role_arn" {
  description = "IAM role ARN for S3 delete handler Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_s3_delete_handler"].arn
}

output "api_search_handler_role_arn" {
  description = "IAM role ARN for API search handler Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_api_search_handler"].arn
}

output "api_fetch_videos_handler_role_arn" {
  description = "IAM role ARN for API fetch videos handler Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_api_fetch_videos_handler"].arn
}

output "api_video_upload_link_handler_role_arn" {
  description = "IAM role ARN for API video upload link handler Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_api_video_upload_link_handler"].arn
}

output "api_fetch_tasks_handler_role_arn" {
  description = "IAM role ARN for API fetch tasks handler Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_api_fetch_tasks_handler"].arn
}

output "sqs_embedding_task_producer_role_arn" {
  description = "IAM role ARN for SQS embedding task producer Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_sqs_embedding_task_producer"].arn
}

output "sqs_embedding_task_consumer_role_arn" {
  description = "IAM role ARN for SQS embedding task consumer Lambda"
  value       = aws_iam_role.lambda_roles["kubrick_sqs_embedding_task_consumer"].arn
}

# Role names (useful for some AWS resources that need names instead of ARNs)
output "lambda_role_names" {
  description = "Names of all Lambda IAM roles"
  value = {
    for role_name, role in aws_iam_role.lambda_roles : role_name => role.name
  }
}

# Custom policy ARNs (for reference or attachment to other resources)
output "secrets_access_policy_arn" {
  description = "ARN of the custom secrets access policy"
  value       = aws_iam_policy.secrets_access.arn
}

# Policy ARN map (useful if other modules need to attach the same policies)
output "policy_arns" {
  description = "Map of all policy ARNs used by this module"
  value       = local.all_policy_arns
  sensitive   = false
}

# Role information with metadata (useful for debugging/documentation)
output "lambda_roles_info" {
  description = "Detailed information about Lambda roles"
  value = {
    for role_name, role in aws_iam_role.lambda_roles : role_name => {
      arn         = role.arn
      name        = role.name
      purpose     = local.lambda_roles[role_name].purpose
      policies    = local.lambda_role_policies[role_name]
    }
  }
}
