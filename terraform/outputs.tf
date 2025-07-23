output "vpc_id" {
  description = "ID of the created VPC"
  value       = module.vpc_network.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the created public subnets"
  value       = module.vpc_network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the created private subnets"
  value       = module.vpc_network.private_subnet_ids
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = module.vpc_network.nat_gateway_id
}
