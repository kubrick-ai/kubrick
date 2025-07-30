locals {
  region          = var.aws_region
  env             = "dev"
  secret          = jsondecode(data.aws_secretsmanager_secret_version.kubrick_secret_version.secret_string)
  embedding_model = "Marengo-retrieval-2.7"
  clip_length     = 6
  min_similarity  = 0.2
  page_limit      = 5
  azs             = data.aws_availability_zones.available.names
}

