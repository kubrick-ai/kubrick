output "vpc_id" {
  description = "The ID of the VPC"
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "VPC public subnets IDs"
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "VPC private subnets IDS"
  value = aws_subnet.private[*].id
}

output "nat_gateway_id" {
  value = aws_nat_gateway.nat.id
}

output "private_subnets_cidrs" {
  description = "VPC private subnet CIDR blocks"
  value       = var.private_subnets_cidrs
}

output "public_subnets_cidrs" {
  description = "VPC private subnet CIDR block"
  value       = var.public_subnets_cidrs
}