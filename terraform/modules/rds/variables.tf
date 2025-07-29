variable "db_name" {
  description = "The name of the database to connect to"
  type        = string
  default     = "kubrick"
}

variable "db_username" {
  description = "The username for the database"
  type        = string
}

variable "db_password" {
  description = "The password for the database"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC in which to create the RDS resources"
  type        = string
}

variable "private_subnet_cidrs" {
  description = "VPC's public subnet CIDR blocks"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "VPC's public subnet CIDR block"
  type        = list(string)
}

variable "db_subnet_ids" {
  description = "A list of subnet IDs for the RDS subnet group"
  type        = list(string)
}

