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

  private_subnet_ids   = module.vpc_network.private_subnet_ids
  db_host              = "your.db.host.address"
  db_username          = local.secrets.database.username
  db_password          = local.secrets.database.password
  embedding_model      = local.embedding_model
  min_similarity       = local.min_similarity
  clip_length          = local.clip_length
  lambda_iam_role_arn  = "arn:aws:iam::123456789012:role/your_lambda_role"
  lambda_sg_id         = "sg-xxxxxxxx"
}


