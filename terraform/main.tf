module "vpc_network" {
  source = "./modules/vpc_network"
  env    = local.env
  region = local.region
}

module "iam" {
  source = "./modules/iam"

  s3_bucket_arn = module.s3.bucket_arn
  environment   = local.env

  depends_on = [module.s3]
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
}

