locals {
  region   = "us-east-2"
  env      = "dev"
  secrets  = jsondecode(data.aws_secretsmanager_secret_version.kubrick_secrets_version.secret_string)
}