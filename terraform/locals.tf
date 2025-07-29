locals {
  region   = "us-east-2"
  env      = "dev"
  secrets  = jsondecode(data.aws_secretsmanager_secret_version.kubrick_secrets_version.secret_string)
  embedding_model = "Marengo-retrieval-2.7"
  clip_length = 6
  min_similarity = 0.2
  page_limit = 5
}