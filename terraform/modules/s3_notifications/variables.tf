variable "kubrick_sqs_embedding_task_producer_arn" {
  description = "ARN of the Lambda function to trigger"
  type        = string
}

variable "bucket_name" {
  type = string
}

variable "lambda_function_arn" {
  type = string
}