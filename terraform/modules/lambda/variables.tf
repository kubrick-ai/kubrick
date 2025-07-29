variable "lambda_iam_role_arn" {
  description = "ARN for the lambda IAM role"
  type        = string
}

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

variable "embedding_model" {
  description = "The embedding model's name"
  type        = string
}

variable "private_subnet_ids" {
  description = "VPC private subnet ids"
  type        = list(string)
}

variable "lambda_sg_id" {
  description = "The security group ID for Lambda access"
  type        = string
}