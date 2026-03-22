"""Pulumi — GCP Infrastructure: GKE + Cloud SQL + Networking."""
import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
project = config.require("gcp_project")
region = config.get("region") or "us-central1"
name = config.get("cluster_name") or "ecommerce-gcp"

network = gcp.compute.Network("vpc", name=f"{name}-vpc", auto_create_subnetworks=False, project=project)
subnet = gcp.compute.Subnetwork("subnet", name=f"{name}-subnet", ip_cidr_range="10.2.0.0/16",
    region=region, network=network.id, project=project,
    secondary_ip_ranges=[
        gcp.compute.SubnetworkSecondaryIpRangeArgs(range_name="pods", ip_cidr_range="10.3.0.0/16"),
        gcp.compute.SubnetworkSecondaryIpRangeArgs(range_name="services", ip_cidr_range="10.4.0.0/20")])

cluster = gcp.container.Cluster("gke", name=name, location=region, project=project,
    network=network.name, subnetwork=subnet.name, initial_node_count=1, remove_default_node_pool=True,
    ip_allocation_policy=gcp.container.ClusterIpAllocationPolicyArgs(
        cluster_secondary_range_name="pods", services_secondary_range_name="services"),
    workload_identity_config=gcp.container.ClusterWorkloadIdentityConfigArgs(workload_pool=f"{project}.svc.id.goog"),
    release_channel=gcp.container.ClusterReleaseChannelArgs(channel="REGULAR"))

nodes = gcp.container.NodePool("nodes", name=f"{name}-pool", cluster=cluster.name,
    location=region, project=project, node_count=2,
    autoscaling=gcp.container.NodePoolAutoscalingArgs(min_node_count=2, max_node_count=6),
    node_config=gcp.container.NodePoolNodeConfigArgs(machine_type="e2-standard-4", disk_size_gb=50,
        oauth_scopes=["https://www.googleapis.com/auth/cloud-platform"]),
    management=gcp.container.NodePoolManagementArgs(auto_repair=True, auto_upgrade=True))

db = gcp.sql.DatabaseInstance("db", name=f"{name}-db", database_version="POSTGRES_15",
    region=region, project=project, deletion_protection=True,
    settings=gcp.sql.DatabaseInstanceSettingsArgs(tier="db-custom-2-8192", availability_type="REGIONAL",
        disk_size=50, disk_autoresize=True, disk_type="PD_SSD",
        backup_configuration=gcp.sql.DatabaseInstanceSettingsBackupConfigurationArgs(
            enabled=True, point_in_time_recovery_enabled=True, start_time="02:00"),
        ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
            ipv4_enabled=False, private_network=network.id)))

pulumi.export("gke_endpoint", cluster.endpoint)
pulumi.export("db_connection", db.connection_name)
