variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to trigger"
  type        = string
}
