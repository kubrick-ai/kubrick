output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.kubrick_playground.id
}

output "cloudfront_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.kubrick_playground.domain_name
}

output "cloudfront_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.kubrick_playground.arn
}

output "cloudfront_status" {
  description = "The current status of the CloudFront distribution"
  value       = aws_cloudfront_distribution.kubrick_playground.status
}
