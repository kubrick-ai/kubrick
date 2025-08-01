variable "api_gateway_write_done" {
  type = any
  description = "Dependency on API Gateway write to .env"
}

variable "cloudfront_domain" {
  description = "The domain name of the CloudFront distribution"
  type        = string
}
