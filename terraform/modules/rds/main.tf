variable "identifier" {
  type = string
}

variable "multi_az" {
  type = bool
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "tags" {
  type = map(string)
}

resource "aws_db_subnet_group" "main" {
  name_prefix = "rds-"
  subnet_ids  = var.subnet_ids
  tags        = var.tags
}

resource "aws_security_group" "rds" {
  name_prefix = "rds-"
  vpc_id      = var.vpc_id
  tags        = var.tags
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_db_instance" "main" {
  identifier           = var.identifier
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  storage_encrypted    = true
  multi_az             = var.multi_az
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  username             = "dbadmin"
  password             = random_password.db_password.result
  skip_final_snapshot  = true
  tags                 = var.tags
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

output "endpoint" {
  value = aws_db_instance.main.endpoint
}
