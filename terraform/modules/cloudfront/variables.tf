variable "s3_bucket_regional_domain_name" {
  description = "The regional domain name of the S3 bucket (e.g. my-bucket.s3.us-east-1.amazonaws.com)"
  type        = string
}

variable "s3_bucket_arn" {
  description = "The ARN of the S3 bucket"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "kubrick_playground_bucket_name" {
  description = "The name of the S3 bucket used to serve the Kubrick playground static website"
  type        = string
}