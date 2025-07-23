variable "env" {
  type        = string
  description = "Environment name (e.g., dev, prod)"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}

variable "azs" {
  type        = list(string)
  description = "Availability zones to use"
}

variable "public_subnets" {
  type        = list(string)
  description = "Public subnet CIDRs"
}

variable "private_subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
  description = "Private subnet CIDRs and AZs"
}

variable "create_isolated_subnets" {
  type        = bool
  description = "Whether to create isolated subnets"
  default     = true
}
