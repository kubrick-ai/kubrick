# Lambda Function ARNs
output "kubrick_api_fetch_videos_handler_arn" {
  description = "ARN of the kubrick_api_fetch_videos_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_fetch_videos_handler.arn
}

output "kubrick_api_search_handler_arn" {
  description = "ARN of the kubrick_api_search_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_search_handler.arn
}

# Lambda Function Invoke ARNs
output "kubrick_api_fetch_videos_handler_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_fetch_videos_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_fetch_videos_handler.invoke_arn
}

output "kubrick_api_search_handler_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_search_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_search_handler.invoke_arn
}

output "kubrick_api_video_upload_link_handler_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_video_upload_link_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_video_upload_link_handler.invoke_arn
}

output "kubrick_api_fetch_tasks_handler_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_fetch_tasks_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_fetch_tasks_handler.invoke_arn
}

# Lambda Function Names
output "kubrick_api_fetch_videos_handler_function_name" {
  description = "Function name of the kubrick_api_fetch_videos_handler Lambda"
  value       = aws_lambda_function.kubrick_api_fetch_videos_handler.function_name
}

output "kubrick_api_search_handler_function_name" {
  description = "Function name of the kubrick_api_search_handler Lambda"
  value       = aws_lambda_function.kubrick_api_search_handler.function_name
}

output "kubrick_api_video_upload_link_handler_function_name" {
  description = "Function name of the kubrick_api_video_upload_link_handler Lambda"
  value       = aws_lambda_function.kubrick_api_video_upload_link_handler.function_name
}

output "kubrick_api_fetch_tasks_handler_function_name" {
  description = "Function name of the kubrick_api_fetch_tasks_handler Lambda"
  value       = aws_lambda_function.kubrick_api_fetch_tasks_handler.function_name
}

# Additional Lambda Function ARNs (for reference)
output "kubrick_s3_delete_handler_arn" {
  description = "ARN of the kubrick_s3_delete_handler Lambda function"
  value       = aws_lambda_function.kubrick_s3_delete_handler.arn
}

output "kubrick_api_video_upload_link_handler_arn" {
  description = "ARN of the kubrick_api_video_upload_link_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_video_upload_link_handler.arn
}

output "kubrick_api_fetch_tasks_handler_arn" {
  description = "ARN of the kubrick_api_fetch_tasks_handler Lambda function"
  value       = aws_lambda_function.kubrick_api_fetch_tasks_handler.arn
}

output "kubrick_sqs_embedding_task_producer_arn" {
  description = "ARN of the kubrick_sqs_embedding_task_producer Lambda function"
  value       = aws_lambda_function.kubrick_sqs_embedding_task_producer.arn
}

output "kubrick_sqs_embedding_task_consumer_arn" {
  description = "ARN of the kubrick_sqs_embedding_task_consumer Lambda function"
  value       = aws_lambda_function.kubrick_sqs_embedding_task_consumer.arn
}
