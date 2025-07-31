output "secret_arn" {
  description = "The ARN of the AWS Secrets Manager secret"
  value       = aws_secretsmanager_secret.kubrick_secret.arn
}

output "secret_id" {
  description = "The ID of the AWS Secrets Manager secret"
  value       = aws_secretsmanager_secret.kubrick_secret.id
}

output "secret_name" {
  description = "The name of the AWS Secrets Manager secret"
  value       = aws_secretsmanager_secret.kubrick_secret.name
}

output "secret_version_id" {
  description = "The version ID of the AWS Secrets Manager secret version"
  value       = aws_secretsmanager_secret_version.kubrick_secret_version.version_id
}
