# Main SQS Queue for embedding tasks
resource "aws_sqs_queue" "embedding_task_queue" {
  name                       = "${var.environment}-embedding-task-queue"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  delay_seconds             = var.delay_seconds
  receive_wait_time_seconds = var.receive_wait_time_seconds

  tags = {
    Name        = "${var.environment}-embedding-task-queue"
    Environment = var.environment
    Purpose     = "Video embedding task processing"
  }
}

# SQS Queue Policy for access control
resource "aws_sqs_queue_policy" "embedding_task_queue_policy" {
  queue_url = aws_sqs_queue.embedding_task_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "__default_policy_ID"
    Statement = [
      {
        Sid    = "__owner_statement"
        Effect = "Allow"
        Principal = {
          AWS = var.queue_policy_principals
        }
        Action   = var.queue_policy_actions
        Resource = aws_sqs_queue.embedding_task_queue.arn
      }
    ]
  })
}
