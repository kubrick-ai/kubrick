resource "aws_db_instance" "kubrick_db" {
  engine                 = "postgres"
  engine_version         = "17.4"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  db_subnet_group_name   = aws_db_subnet_group.kubrick_db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.kubrick_db_sg.id]
  username               = var.db_username
  password               = var.db_password
  db_name                = var.db_name
  identifier             = "kubrick-database"
  skip_final_snapshot    = true

  tags = {
    Name = "kubrick-db"
  }
}

resource "aws_db_subnet_group" "kubrick_db_subnet_group" {
  name       = "kubrick-db-subnet-group"
  subnet_ids = var.db_subnet_ids

  tags = {
    Name = "kubrick-db-subnet-group"
  }
}

resource "aws_security_group" "kubrick_db_sg" {
  name        = "kubrick-db-sg"
  description = "Allow access to the kubrick database"
  vpc_id      = var.vpc_id

  tags = {
    Name = "allow_private_subnet_access_to_rds"
  }

  ingress {
    from_port         = 5432
    to_port           = 5432
    protocol          = "tcp"
    cidr_blocks       = var.private_subnet_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [
      var.private_subnet_cidrs[0],
      var.private_subnet_cidrs[1],
      var.public_subnet_cidrs[0],
      var.public_subnet_cidrs[1],
    ]
  }
}