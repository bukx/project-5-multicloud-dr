variable "project" {
  type = string
}

variable "tags" {
  type = map(string)
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags       = merge(var.tags, { Name = "${var.project}-vpc" })
}

resource "aws_subnet" "private" {
  count            = 2
  vpc_id            = aws_vpc.main.id
  cidr_block       = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = merge(var.tags, { Name = "${var.project}-private-subnet-${count.index + 1}" })
}

data "aws_availability_zones" "available" {
  state = "available"
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}
