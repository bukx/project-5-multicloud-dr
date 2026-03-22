# Project 5: Multi-Cloud Infrastructure with Automated Disaster Recovery

## Tools: Terraform, Pulumi, Ansible, Kubernetes (EKS/AKS/GKE), Docker, Route 53, Datadog, CloudWatch, Azure Monitor, GCP Monitoring, Python, Bash, PostgreSQL

## Quick Start
```bash
# Provision AWS
cd terraform/aws/environments/prod && terraform init && terraform apply

# Provision Azure
cd terraform/azure/environments/prod && terraform init && terraform apply

# Provision GCP
cd pulumi/gcp && pulumi up

# Configure Ansible across all clouds
ansible-playbook -i ansible/inventory ansible/roles/hardening/site.yml

# Run DR drill
python dr-scripts/failover.py --target azure --reason "DR drill" --dry-run
python dr-scripts/failover.py --target azure --reason "DR drill"
python dr-scripts/failover.py --target aws --reason "Restore primary"
```

## Success Metrics
- Same app on all 3 clouds simultaneously
- DR failover: <60 seconds DNS propagation
- Unified Datadog dashboard across AWS/Azure/GCP
- Automated failover with Slack + Datadog notifications
