# 🌍 Multi-Cloud Infrastructure with Automated Disaster Recovery

![Validate](https://github.com/bukx/project-5-multicloud-dr/actions/workflows/validate.yml/badge.svg)

![AWS](https://img.shields.io/badge/AWS-FF9900?style=flat&logo=amazonaws&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![GCP](https://img.shields.io/badge/GCP-4285F4?style=flat&logo=googlecloud&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat&logo=terraform&logoColor=white)
![Pulumi](https://img.shields.io/badge/Pulumi-8A3391?style=flat&logo=pulumi&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)

Production multi-cloud deployment across **AWS, Azure, and GCP** with **automated disaster recovery failover**, unified monitoring via **Datadog**, and infrastructure provisioned with both **Terraform** and **Pulumi**.

---

## 🏗 Architecture

![Architecture Diagram](docs/architecture.png)

## 🔧 Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| AWS IaC | **Terraform** | EKS, VPC, RDS provisioning |
| Azure IaC | **Terraform** | AKS, VNet provisioning |
| GCP IaC | **Pulumi (Python)** | GKE, VPC provisioning |
| Orchestration | **EKS / AKS / GKE** | Multi-cloud Kubernetes |
| Hardening | **Ansible** | CIS benchmark across all clouds |
| Monitoring | **Datadog** | Unified dashboard across all providers |
| DR Automation | **Python** | Automated failover with health checks |
| DNS | **Route 53** | Global traffic management + failover |

## 🚀 Quick Start

```bash
# Provision AWS (primary)
cd terraform/aws/environments/prod && terraform init && terraform apply

# Provision Azure (standby)
cd terraform/azure/environments/prod && terraform init && terraform apply

# Provision GCP (standby)
cd pulumi/gcp && pulumi up

# Harden all hosts
ansible-playbook -i ansible/inventory ansible/roles/hardening/site.yml

# DR drill (dry-run first)
python dr-scripts/failover.py --target azure --reason "DR drill" --dry-run
python dr-scripts/failover.py --target azure --reason "DR drill"

# Restore primary
python dr-scripts/failover.py --target aws --reason "Restore primary"
```

## 📈 Key Outcomes

| Metric | Result |
|--------|--------|
| Multi-cloud parity | Same app running on AWS, Azure, and GCP |
| DR failover time | < 60 seconds DNS propagation |
| Monitoring coverage | Unified Datadog dashboard across all clouds |
| Failover automation | One-command with Slack notifications |

## 📁 Project Structure

```
├── ansible/                      # CIS hardening playbooks
├── app/                          # Application source + Dockerfile
├── dr-scripts/                   # Automated failover scripts
├── k8s/
│   ├── aws/                      # EKS deployment manifests
│   ├── azure/                    # AKS deployment manifests
│   └── gcp/                      # GKE deployment manifests
├── monitoring/datadog/           # Datadog dashboard config
├── pulumi/gcp/                   # GCP infrastructure (Pulumi)
└── terraform/
    ├── aws/environments/prod/    # AWS infrastructure
    └── azure/environments/prod/  # Azure infrastructure
```

## 📜 License

This project is for portfolio/demonstration purposes.
