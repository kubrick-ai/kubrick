module "secrets_manager" {
  source             = "./modules/secrets_manager"
  name               = var.secrets_manager_name
  description        = "Secret store for Kubrick application"
  environment        = local.env
  db_username        = var.db_username
  db_password        = var.db_password
  twelvelabs_api_key = var.twelvelabs_api_key
}

module "vpc_network" {
  source = "./modules/vpc_network"
  env    = local.env
  region = local.region
  azs    = local.azs
}

module "iam" {
  source                   = "./modules/iam"
  secret_arn               = module.secrets_manager.secret_arn
  environment              = local.env
  embedding_task_queue_arn = module.sqs.queue_arn

  depends_on = [module.secrets_manager]
}

# Public S3 bucket depends on API_Gateway
module "s3" {
  source = "./modules/s3"

  api_gateway_write_done = module.api_gateway.null_resource_write_api_url_to_env
  cloudfront_domain      = module.cloudfront.cloudfront_domain_name
}

module "s3_notifications" {
  source                      = "./modules/s3_notifications"
  bucket_id                   = module.s3.bucket_id
  create_lambda_function_arn  = module.lambda.kubrick_sqs_embedding_task_producer_arn
  create_lambda_function_name = module.lambda.kubrick_sqs_embedding_task_producer_function_name
  delete_lambda_function_arn  = module.lambda.kubrick_s3_delete_handler_arn
  delete_lambda_function_name = module.lambda.kubrick_s3_delete_handler_function_name
  bucket_arn                  = module.s3.bucket_arn

  depends_on = [module.lambda, module.s3]
}

module "rds" {
  source               = "./modules/rds"
  db_username          = local.secret.DB_USERNAME
  db_password          = local.secret.DB_PASSWORD
  vpc_id               = module.vpc_network.vpc_id
  db_subnet_ids        = module.vpc_network.private_subnet_ids
  public_subnet_cidrs  = module.vpc_network.public_subnets_cidrs
  private_subnet_cidrs = module.vpc_network.private_subnets_cidrs
}

module "lambda" {
  source = "./modules/lambda"

  aws_region                                        = local.region
  lambda_iam_db_bootstrap_role_arn                  = module.iam.db_bootstrap_role_arn
  lambda_iam_s3_delete_handler_role_arn             = module.iam.s3_delete_handler_role_arn
  lambda_iam_api_search_handler_role_arn            = module.iam.api_search_handler_role_arn
  lambda_iam_api_fetch_videos_handler_role_arn      = module.iam.api_fetch_videos_handler_role_arn
  lambda_iam_api_video_upload_link_handler_role_arn = module.iam.api_video_upload_link_handler_role_arn
  lambda_iam_api_fetch_tasks_handler_role_arn       = module.iam.api_fetch_tasks_handler_role_arn
  lambda_iam_sqs_embedding_task_producer_role_arn   = module.iam.sqs_embedding_task_producer_role_arn
  lambda_iam_sqs_embedding_task_consumer_role_arn   = module.iam.sqs_embedding_task_consumer_role_arn
  db_host                                           = module.rds.db_host
  db_username                                       = local.secret.DB_USERNAME
  db_password                                       = local.secret.DB_PASSWORD
  embedding_model                                   = local.embedding_model
  min_similarity                                    = local.min_similarity
  page_limit                                        = local.page_limit
  clip_length                                       = local.clip_length
  query_media_file_size_limit                       = local.query_media_file_size_limit
  default_task_limit                                = local.default_task_limit
  max_task_limit                                    = local.max_task_limit
  default_task_page                                 = local.default_task_page
  presigned_url_expiry                              = local.presigned_url_expiry
  presigned_url_ttl                                 = local.presigned_url_ttl
  file_check_retries                                = local.file_check_retries
  file_check_delay_sec                              = local.file_check_delay_sec
  video_embedding_scopes                            = local.video_embedding_scopes
  private_subnet_ids                                = module.vpc_network.private_subnet_ids
  vpc_id                                            = module.vpc_network.vpc_id
  s3_bucket_name                                    = module.s3.kubrick_video_upload_bucket_name
  queue_url                                         = module.sqs.queue_url
  queue_arn                                         = module.sqs.queue_arn
  secrets_manager_name                              = var.secrets_manager_name
  aws_profile                                       = var.aws_profile

  depends_on = [
    module.rds, module.iam, module.sqs
  ]
}

module "sqs" {
  source                  = "./modules/sqs"
  environment             = local.env
  enable_queue_policy     = true
  queue_policy_principals = ["arn:aws:iam::791237609017:root"]
  queue_policy_actions    = ["SQS:*"]
}

module "api_gateway" {
  source                            = "./modules/api_gateway"
  fetch_videos_lambda_invoke_arn    = module.lambda.kubrick_api_fetch_videos_handler_invoke_arn
  search_lambda_invoke_arn          = module.lambda.kubrick_api_search_handler_invoke_arn
  upload_link_lambda_invoke_arn     = module.lambda.kubrick_api_video_upload_link_handler_invoke_arn
  fetch_tasks_lambda_invoke_arn     = module.lambda.kubrick_api_fetch_tasks_handler_invoke_arn
  fetch_videos_lambda_function_name = module.lambda.kubrick_api_fetch_videos_handler_function_name
  search_lambda_function_name       = module.lambda.kubrick_api_search_handler_function_name
  upload_link_lambda_function_name  = module.lambda.kubrick_api_video_upload_link_handler_function_name
  fetch_tasks_lambda_function_name  = module.lambda.kubrick_api_fetch_tasks_handler_function_name
  aws_region                        = local.region

  depends_on = [module.lambda]
}

module "cloudfront" {
  source                         = "./modules/cloudfront"
  s3_bucket_regional_domain_name = module.s3.kubrick_playground_bucket_regional_domain_name
  s3_bucket_arn                  = module.s3.kubrick_playground_bucket_arn
  aws_region                     = local.region
  kubrick_playground_bucket_name = module.s3.kubrick_playground_bucket_name
}
