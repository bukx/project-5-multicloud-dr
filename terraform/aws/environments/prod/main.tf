terraform {
  required_version = ">= 1.5"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
  backend "s3" { bucket = "multicloud-dr-tfstate"; key = "aws/prod/terraform.tfstate"; region = "us-east-1"; encrypt = true }
}
provider "aws" { region = "us-east-1" }
locals { project = "multicloud-dr"; tags = { Project = local.project, ManagedBy = "terraform", Cloud = "aws" } }

module "eks" {
  source = "../../modules/eks"
  cluster_name = "${local.project}-aws"; vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids; tags = local.tags
}

module "rds" {
  source = "../../modules/rds"
  identifier = "${local.project}-db-aws"; multi_az = true
  vpc_id = module.vpc.vpc_id; subnet_ids = module.vpc.private_subnet_ids; tags = local.tags
}

resource "aws_route53_health_check" "aws" {
  fqdn = "app-aws.example.com"; port = 443; type = "HTTPS"
  resource_path = "/health"; request_interval = 10; failure_threshold = 3
  tags = merge(local.tags, { Name = "aws-primary-health" })
}

resource "aws_route53_record" "primary" {
  zone_id = var.hosted_zone_id; name = "app.example.com"; type = "A"
  failover_routing_policy { type = "PRIMARY" }
  set_identifier = "aws-primary"; health_check_id = aws_route53_health_check.aws.id
  alias { name = module.eks.alb_dns; zone_id = module.eks.alb_zone_id; evaluate_target_health = true }
}

resource "aws_route53_record" "secondary" {
  zone_id = var.hosted_zone_id; name = "app.example.com"; type = "A"; ttl = 60
  failover_routing_policy { type = "SECONDARY" }
  set_identifier = "azure-secondary"; records = [var.azure_lb_ip]
}

variable "hosted_zone_id" { type = string }
variable "azure_lb_ip" { type = string }
output "eks_endpoint" { value = module.eks.cluster_endpoint }
output "rds_endpoint" { value = module.rds.endpoint }
