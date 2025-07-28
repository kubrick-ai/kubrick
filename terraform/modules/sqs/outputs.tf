output "queue_url" {
  description = "The URL of the main SQS queue"
  value       = aws_sqs_queue.embedding_task_queue.url
}

output "queue_arn" {
  description = "The ARN of the main SQS queue"
  value       = aws_sqs_queue.embedding_task_queue.arn
}

output "queue_name" {
  description = "The name of the main SQS queue"
  value       = aws_sqs_queue.embedding_task_queue.name
}
