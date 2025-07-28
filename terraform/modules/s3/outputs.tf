output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.kubrick_video_upload_bucket.bucket
}

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
