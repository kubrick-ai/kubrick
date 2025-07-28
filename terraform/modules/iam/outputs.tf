output "lambda_s3_readonly_role_arn" {
  description = "ARN of the Lambda S3 read-only IAM role"
  value       = aws_iam_role.lambda_s3_readonly.arn
}

output "lambda_s3_readonly_role_name" {
  description = "Name of the Lambda S3 read-only IAM role"
  value       = aws_iam_role.lambda_s3_readonly.name
}

output "lambda_s3_full_access_role_arn" {
  description = "ARN of the Lambda S3 full access IAM role"
  value       = aws_iam_role.lambda_s3_full_access.arn
}

output "lambda_s3_full_access_role_name" {
  description = "Name of the Lambda S3 full access IAM role"
  value       = aws_iam_role.lambda_s3_full_access.name
}

output "lambda_s3_readonly_policy_arn" {
  description = "ARN of the Lambda S3 read-only policy"
  value       = aws_iam_policy.lambda_s3_readonly.arn
}

output "lambda_s3_full_access_policy_arn" {
  description = "ARN of the Lambda S3 full access policy"
  value       = aws_iam_policy.lambda_s3_full_access.arn
}
