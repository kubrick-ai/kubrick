variable "db_host" {
  description = "The endpoint of the RDS database"
  type        = string
}

variable "db_username" {
  description = "The username for the RDS database"
  type        = string
}

variable "db_password" {
  description = "The username for the RDS database"
  type        = string
}

variable "clip_length" {
  description = "The default clip length for embeddings"
  type        = number
}

variable "min_similarity" {
  description = "The minimum similarity value when searching"
  type        = number
}

variable "page_limit" {
  description = "The default clips in a page"
  type        = number
}

variable "embedding_model" {
  description = "The embedding model's name"
  type        = string
}

variable "query_media_file_size_limit" {
  description = "Maximum file size for media queries"
  type        = number
}

variable "default_task_limit" {
  description = "Default limit for task queries"
  type        = number
}

variable "max_task_limit" {
  description = "Maximum limit for task queries"
  type        = number
}

variable "default_task_page" {
  description = "Default page number for task queries"
  type        = number
}

variable "presigned_url_expiry" {
  description = "Expiry time for presigned URLs in seconds"
  type        = number
}

variable "presigned_url_ttl" {
  description = "TTL for presigned URLs in seconds"
  type        = number
}

variable "file_check_retries" {
  description = "Number of retries for file checks"
  type        = number
}

variable "file_check_delay_sec" {
  description = "Delay between file check retries in seconds"
  type        = number
}

variable "video_embedding_scopes" {
  description = "Scopes for video embeddings"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "VPC private subnet ids"
  type        = list(string)
}

variable "vpc_id" {
  description = "The ID of the VPC where the Lambda and security groups will be created"
  type        = string
}

#
# variable "lambda_sg_id" {
#   description = "The security group ID for Lambda access"
#   type        = string
# }

variable "lambda_iam_db_bootstrap_role_arn" {
  description = "IAM role ARN for database initialisation Lambda"
  type        = string
}

variable "lambda_iam_s3_delete_handler_role_arn" {
  description = "IAM role ARN for S3 delete handler Lambda"
  type        = string
}

variable "lambda_iam_api_search_handler_role_arn" {
  description = "IAM role ARN for API search handler Lambda"
  type        = string
}

variable "lambda_iam_api_fetch_videos_handler_role_arn" {
  description = "IAM role ARN for API fetch videos handler Lambda"
  type        = string
}

variable "lambda_iam_api_video_upload_link_handler_role_arn" {
  description = "IAM role ARN for API video upload link handler Lambda"
  type        = string
}

variable "lambda_iam_api_fetch_tasks_handler_role_arn" {
  description = "IAM role ARN for API fetch tasks handler Lambda"
  type        = string
}

variable "lambda_iam_sqs_embedding_task_producer_role_arn" {
  description = "IAM role ARN for SQS embedding task producer Lambda"
  type        = string
}

variable "lambda_iam_sqs_embedding_task_consumer_role_arn" {
  description = "IAM role ARN for SQS embedding task consumer Lambda"
  type        = string
}

variable "s3_bucket_name" {
  description = "The name to the S3 Bucket"
  type        = string
}

variable "queue_url" {
  description = "The URL of the main SQS queue"
  type        = string
}

variable "queue_arn" {
  description = "ARN of the SQS queue to trigger the embedding task consumer"
  type        = string
}