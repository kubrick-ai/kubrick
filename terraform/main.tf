module "vpc_network" {
  source = "./modules/vpc-network"

  env                     = local.env
  vpc_cidr                = var.vpc_cidr
  azs                     = var.azs
  public_subnets          = var.public_subnets
  private_subnets         = var.private_subnets
  create_isolated_subnets = var.create_isolated_subnets
}
