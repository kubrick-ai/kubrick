output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.kubrick_video_upload_bucket.arn
}

output "bucket_id" {
  description = "ID of the S3 bucket"
  value       = aws_s3_bucket.kubrick_video_upload_bucket.id
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.kubrick_video_upload_bucket.bucket_domain_name
}

output "kubrick_video_upload_bucket_name" {
  value = aws_s3_bucket.kubrick_video_upload_bucket.bucket
}

output "kubrick_playground_bucket_name" {
  value = aws_s3_bucket.kubrick_playground_bucket.bucket
}

output "kubrick_playground_bucket_regional_domain_name" {
  value = aws_s3_bucket.kubrick_playground_bucket.bucket_regional_domain_name
}

output "kubrick_playground_bucket_website_endpoint" {
  value = aws_s3_bucket_website_configuration.kubrick_playground_bucket.website_endpoint
}

output "kubrick_playground_bucket_arn" {
  value = aws_s3_bucket.kubrick_playground_bucket.arn
}

