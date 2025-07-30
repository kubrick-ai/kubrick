variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "visibility_timeout_seconds" {
  description = "The visibility timeout for the queue in seconds"
  type        = number
  default     = 960  
}

variable "message_retention_seconds" {
  description = "The number of seconds Amazon SQS retains a message"
  type        = number
  default     = 14400
}

variable "delay_seconds" {
  description = "The time in seconds that the delivery of all messages in the queue will be delayed"
  type        = number
  default     = 10
}

variable "receive_wait_time_seconds" {
  description = "The time for which a ReceiveMessage call will wait for a message to arrive"
  type        = number
  default     = 0
}

variable "enable_queue_policy" {
  description = "Whether to attach an access policy to the SQS queue"
  type        = bool
  default     = true
}

variable "queue_policy_principals" {
  description = "List of AWS principals (ARNs) that should have access to the queue. Required when enable_queue_policy is true."
  type        = list(string)
  default     = []
}

variable "queue_policy_actions" {
  description = "List of SQS actions to allow in the queue policy"
  type        = list(string)
  default     = ["SQS:*"]
}
