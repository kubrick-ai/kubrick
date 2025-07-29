module "vpc_network" {
  source = "./modules/vpc_network"
  env    = local.env
  region = local.region
}

module "iam" {
  source                   = "./modules/iam"
  secret_arn               = data.aws_secretsmanager_secret.kubrick_secrets.arn
  s3_bucket_arn            = module.s3.bucket_arn
  environment              = local.env
  embedding_task_queue_arn = "placeholder" # Need to fill this out when merged with sqs

  depends_on               = [module.s3]
}

module "s3" {
  source = "./modules/s3"
}

module "rds" {
  source               = "./modules/rds"
  db_username          = local.secrets.database.username
  db_password          = local.secrets.database.password
  vpc_id               = module.vpc_network.vpc_id
  db_subnet_ids        = module.vpc_network.private_subnet_ids
  public_subnet_cidrs  = module.vpc_network.public_subnets_cidrs
  private_subnet_cidrs = module.vpc_network.private_subnets_cidrs
}

module "lambda" {
  source = "./modules/lambda"
  lambda_iam_s3_delete_handler_role_arn             = module.iam.s3_delete_handler_role_arn
  lambda_iam_api_search_handler_role_arn            = module.iam.api_search_handler_role_arn
  lambda_iam_api_fetch_videos_handler_role_arn      = module.iam.api_fetch_videos_handler_role_arn
  lambda_iam_api_video_upload_link_handler_role_arn = module.iam.api_video_upload_link_handler_role_arn
  lambda_iam_api_fetch_tasks_handler_role_arn       = module.iam.api_fetch_tasks_handler_role_arn
  lambda_iam_sqs_embedding_task_producer_role_arn   = module.iam.sqs_embedding_task_producer_role_arn
  lambda_iam_sqs_embedding_task_consumer_role_arn   = module.iam.sqs_embedding_task_consumer_role_arn
  db_host                                           = module.rds.db_host
  db_username                                       = local.secrets.database.username
  db_password                                       = local.secrets.database.password
  embedding_model                                   = local.embedding_model
  min_similarity                                    = local.min_similarity
  page_limit                                        = local.page_limit 
  clip_length                                       = local.clip_length
  private_subnet_ids                                = module.vpc_network.private_subnet_ids
  vpc_id                                            = module.vpc_network.vpc_id
  s3_bucket_name                                    = module.s3.bucket_name
}


