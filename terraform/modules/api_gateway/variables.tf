variable "api_name" {
  description = "The name of the API Gateway REST API"
  type        = string
  default     = "kubrick-api"
}

variable "videos_path" {
  description = "The 'videos' endpoint for the API"
  type        = string
  default     = "videos"
}

variable "search_path" {
  description = "The 'search' endpoint for the API"
  type        = string
  default     = "search"
}

variable "generate_upload_link_path" {
  description = "The 'generate-upload-link' endpoint for the API"
  type        = string
  default     = "generate-upload-link"
}

variable "fetch_videos_lambda_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_fetch_videos_handler Lambda function"
  type        = string
}

variable "search_lambda_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_search_handler Lambda function"
  type        = string
}

variable "fetch_videos_lambda_function_name" {
  description = "Function name of the kubrick_api_fetch_videos_handler Lambda"
  type        = string
}

variable "search_lambda_function_name" {
  description = "Function name of the kubrick_api_search_handler Lambda"
  type        = string
}

variable "upload_link_lambda_invoke_arn" {
  description = "Invoke ARN of the kubrick_api_video_upload_link_handler Lambda function"
  type        = string
}

variable "upload_link_lambda_function_name" {
  description = "Function name of the kubrick_api_video_upload_link_handler Lambda"
  type        = string
}

variable "aws_region" {
  description = "AWS region for API Gateway outputs"
  type        = string
}

variable "stage_name" {
  description = "API Gateway deployment stage name"
  type        = string
  default     = "dev"
}
