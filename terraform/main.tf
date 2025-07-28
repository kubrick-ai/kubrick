module "vpc_network" {
  source = "./modules/vpc_network"
  env    = local.env
  region = local.region
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