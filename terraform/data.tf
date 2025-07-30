data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_secretsmanager_secret" "kubrick_secrets" {
  name = var.secrets_manager_name
}

data "aws_secretsmanager_secret_version" "kubrick_secrets_version" {
  secret_id = data.aws_secretsmanager_secret.kubrick_secrets.id
}