output "db_host" {
  description = "Hostname for the Kubrick RDS PostgreSQL database"
  value       = aws_db_instance.kubrick_db.address
}

output "db_name" {
  description = "The name of the Kubrick RDS database"
  value       = aws_db_instance.kubrick_db.db_name
}