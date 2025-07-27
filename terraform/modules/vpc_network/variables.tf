 variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets_cidrs" {
  description = "CIDR block for the public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets_cidrs" {
  description = "The CIDR blocks for the private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "azs" {
  type        = list(string)
  description = "Availability zones to use"
  default     = ["us-east-2a", "us-east-2b"]
}

variable "env" {
  type        = string
  description = "Environment name (e.g., dev, prod)"
}