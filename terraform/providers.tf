provider "aws" {
  region  = local.region
  profile = "AdministratorAccess-791237609017-Dom"
}

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}