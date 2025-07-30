module "vpc_network" {
  source = "./modules/vpc_network"
  env    = local.env
  region = local.region
  azs    = local.azs
}

module "iam" {
  source                   = "./modules/iam"
  secret_arn               = data.aws_secretsmanager_secret.kubrick_secrets.arn
  environment              = local.env
  embedding_task_queue_arn = module.sqs.queue_arn
}

module "s3" {
  source = "./modules/s3"
}

# kubrick_sqs_embedding_task_producer_function
# kubrick_s3_delete_handler_function
module "s3_notifications" {
  source = "./modules/s3_notifications"
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
  db_username          = local.secrets.DB_USERNAME
  db_password          = local.secrets.DB_PASSWORD
  vpc_id               = module.vpc_network.vpc_id
  db_subnet_ids        = module.vpc_network.private_subnet_ids
  public_subnet_cidrs  = module.vpc_network.public_subnets_cidrs
  private_subnet_cidrs = module.vpc_network.private_subnets_cidrs
}

module "lambda" {
  source                                            = "./modules/lambda"
  lambda_iam_db_bootstrap_role_arn                  = module.iam.db_bootstrap_role_arn
  lambda_iam_s3_delete_handler_role_arn             = module.iam.s3_delete_handler_role_arn
  lambda_iam_api_search_handler_role_arn            = module.iam.api_search_handler_role_arn
  lambda_iam_api_fetch_videos_handler_role_arn      = module.iam.api_fetch_videos_handler_role_arn
  lambda_iam_api_video_upload_link_handler_role_arn = module.iam.api_video_upload_link_handler_role_arn
  lambda_iam_api_fetch_tasks_handler_role_arn       = module.iam.api_fetch_tasks_handler_role_arn
  lambda_iam_sqs_embedding_task_producer_role_arn   = module.iam.sqs_embedding_task_producer_role_arn
  lambda_iam_sqs_embedding_task_consumer_role_arn   = module.iam.sqs_embedding_task_consumer_role_arn
  db_host                                           = module.rds.db_host
  db_username                                       = local.secrets.DB_USERNAME
  db_password                                       = local.secrets.DB_PASSWORD
  embedding_model                                   = local.embedding_model
  min_similarity                                    = local.min_similarity
  page_limit                                        = local.page_limit
  clip_length                                       = local.clip_length
  private_subnet_ids                                = module.vpc_network.private_subnet_ids
  vpc_id                                            = module.vpc_network.vpc_id
  s3_bucket_name                                    = module.s3.bucket_name
  queue_url                                         = module.sqs.queue_url
  queue_arn                                         = module.sqs.queue_arn


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
  source                              = "./modules/api_gateway"
  fetch_videos_lambda_invoke_arn      = module.lambda.kubrick_api_fetch_videos_handler_invoke_arn
  search_lambda_invoke_arn            = module.lambda.kubrick_api_search_handler_invoke_arn
  upload_link_lambda_invoke_arn       = module.lambda.kubrick_api_video_upload_link_handler_invoke_arn
  fetch_tasks_lambda_invoke_arn       = module.lambda.kubrick_api_fetch_tasks_handler_invoke_arn
  fetch_videos_lambda_function_name   = module.lambda.kubrick_api_fetch_videos_handler_function_name
  search_lambda_function_name         = module.lambda.kubrick_api_search_handler_function_name
  upload_link_lambda_function_name    = module.lambda.kubrick_api_video_upload_link_handler_function_name
  fetch_tasks_lambda_function_name    = module.lambda.kubrick_api_fetch_tasks_handler_function_name
  aws_region                          = local.region

  depends_on = [module.lambda]
}
