variable "table_name_prefix" {
  description = "Prefix for DynamoDB table name"
  type        = string
  default     = "kubrick_embedding_cache"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB table"
  type        = bool
  default     = true
}

variable "ttl_days" {
  description = "Number of days to keep cached embeddings before TTL cleanup"
  type        = number
  default     = 30
}