output "table_name" {
  description = "Name of the DynamoDB embeddings cache table"
  value       = aws_dynamodb_table.embeddings_cache.name
}

output "table_arn" {
  description = "ARN of the DynamoDB embeddings cache table"
  value       = aws_dynamodb_table.embeddings_cache.arn
}

output "table_id" {
  description = "ID of the DynamoDB embeddings cache table"
  value       = aws_dynamodb_table.embeddings_cache.id
}