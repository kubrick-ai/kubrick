# AWS Secrets Manager Secret
resource "aws_secretsmanager_secret" "kubrick_secret" {
  name        = var.name
  description = var.description

  tags = {
    Name        = var.name
    Environment = var.environment
  }

  lifecycle {
    # the secret will not be destroyed on terraform destroy
    prevent_destroy = true
    # if var.name is changed, the secret will not be created and destroyed
    ignore_changes = [name]
  }
}


# AWS Secrets Manager Secret Version
resource "aws_secretsmanager_secret_version" "kubrick_secret_version" {
  secret_id = aws_secretsmanager_secret.kubrick_secret.id
  secret_string = jsonencode({
    DB_USERNAME        = var.db_username
    DB_PASSWORD        = var.db_password
    TWELVELABS_API_KEY = var.twelvelabs_api_key
  })
}
