variable "create_lambda_function_arn" {
  description = "ARN of the kubrick_sqs_embedding_task_producer_function to trigger"
  type        = string
}

variable "create_lambda_function_name" {
  description = "kubrick_sqs_embedding_task_producer_function name"
  type        = string
}

variable "delete_lambda_function_arn" {
  description = "ARN of the kubrick_s3_delete_handler_function to trigger"
  type        = string
}

variable "delete_lambda_function_name" {
  description = "kubrick_s3_delete_handler_function name"
  type        = string
}

variable "bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "bucket_id" {
  description = "ID of the S3 bucket"
  type        = string
}