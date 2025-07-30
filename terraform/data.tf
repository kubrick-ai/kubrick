data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_secretsmanager_secret" "kubrick_secret" {
  name = var.secrets_manager_name
}

data "aws_secretsmanager_secret_version" "kubrick_secret_version" {
  secret_id = data.aws_secretsmanager_secret.kubrick_secret.id
}

