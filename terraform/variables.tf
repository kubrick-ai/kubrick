variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "azs" {
  type        = list(string)
  description = "Availability zones to use"
  default     = ["us-east-2a", "us-east-2b"]
}

variable "public_subnets" {
  type        = list(string)
  description = "Public subnet CIDRs"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
  description = "Private subnet CIDRs and AZs"
  default = {
    private_1 = {
      cidr = "10.0.101.0/24"
      az   = "us-east-2a"
    }
    private_2 = {
      cidr = "10.0.102.0/24"
      az   = "us-east-2b"
    }
  }
}

variable "create_isolated_subnets" {
  type        = bool
  default     = true
  description = "Whether to create isolated subnets"
}
