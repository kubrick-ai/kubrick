# DynamoDB table for embedding cache
resource "aws_dynamodb_table" "embeddings_cache" {
  name         = var.table_name_prefix
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "content_hash"
  range_key    = "embedding_config"

  attribute {
    name = "content_hash"
    type = "S"
  }

  attribute {
    name = "embedding_config"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  # Global Secondary Index for querying by creation time
  global_secondary_index {
    name            = "CreatedAtIndex"
    hash_key        = "created_at"
    projection_type = "ALL"
  }


  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }


  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = var.table_name_prefix
    Environment = var.environment
    Purpose     = "Embedding cache for Kubrick application"
  }
}

