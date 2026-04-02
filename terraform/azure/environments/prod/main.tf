terraform {
  required_version = ">= 1.5"
  required_providers { azurerm = { source = "hashicorp/azurerm", version = "~> 3.80" } }
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "multicloudtfstate"
    container_name       = "tfstate"
    key                  = "azure/prod/terraform.tfstate"
  }
}
provider "azurerm" {
  features {}
}

locals {
  project = "multicloud-dr"
  tags = {
    Project   = local.project
    ManagedBy = "terraform"
    Cloud     = "azure"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "${local.project}-rg"
  location = "East US"
  tags     = local.tags
}

resource "azurerm_virtual_network" "main" {
  name                = "${local.project}-vnet"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = ["10.1.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.1.1.0/24"]
}

resource "azurerm_kubernetes_cluster" "main" {
  name                = "${local.project}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = local.project
  kubernetes_version  = "1.29"

  default_node_pool {
    name                = "default"
    node_count          = 3
    vm_size             = "Standard_D4s_v3"
    vnet_subnet_id      = azurerm_subnet.aks.id
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 6
  }

  identity { type = "SystemAssigned" }

  network_profile {
    network_plugin = "azure"
    network_policy = "calico"
  }

  tags = local.tags
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${local.project}-db"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  administrator_login    = "dbadmin"
  administrator_password = var.db_password
  version                = "15"
  sku_name               = "GP_Standard_D2s_v3"
  storage_mb             = 65536
  zone                   = "1"
  tags                   = local.tags

  high_availability { mode = "ZoneRedundant" }
  backup_retention_days        = 7
  geo_redundant_backup_enabled = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "db_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}
