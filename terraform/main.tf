module "vpc_network" {
  source = "./modules/vpc_network"

  env                     = local.env
  region                  = local.region
}
module "s3" {
  source = "./modules/s3"
}

module "iam" {
  source = "./modules/iam"

  s3_bucket_arn = module.s3.bucket_arn
  environment   = local.env

  depends_on = [module.s3]
}
