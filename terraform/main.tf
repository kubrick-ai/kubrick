module "vpc_network" {
  source = "./modules/vpc_network"

  env                     = local.env
  region                  = local.region
}
