locals {
  region = var.aws_region
  env    = "dev"
  secret = {
    DB_USERNAME        = var.db_username
    DB_PASSWORD        = var.db_password
    TWELVELABS_API_KEY = var.twelvelabs_api_key
  }

  # Application configuration defaults
  embedding_model             = "Marengo-retrieval-2.7"
  clip_length                 = 6
  min_similarity              = 0.2
  page_limit                  = 5
  query_media_file_size_limit = 6000000
  default_task_limit          = 10
  max_task_limit              = 50
  default_task_page           = 0
  presigned_url_expiry        = 86400
  presigned_url_ttl           = 600
  file_check_retries          = 2
  file_check_delay_sec        = 2.0
  video_embedding_scopes      = ["clip", "video"]

  azs = data.aws_availability_zones.available.names
}
