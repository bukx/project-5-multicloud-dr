#!/usr/bin/env python3
"""
DR Failover Script — Automates failover between AWS, Azure, and GCP.
Usage:
    python failover.py --target azure --reason "AWS outage"
    python failover.py --target aws --reason "Restore primary"
    python failover.py --target gcp --dry-run --reason "DR drill"
"""
import os
import sys
import time
import argparse
import logging
import requests
import boto3
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dr-failover")

CLOUDS = {
    "aws": {
        "region": "us-east-1",
        "health": "https://app-aws.example.com/health",
        "alb_dns": os.getenv("AWS_ALB_DNS", "aws-alb.us-east-1.elb.amazonaws.com"),
        "alb_zone": os.getenv("AWS_ALB_ZONE", "Z35SXDOTRQ7X7K"),
    },
    "azure": {
        "region": "eastus",
        "health": "https://app-azure.example.com/health",
        "ip": os.getenv("AZURE_LB_IP", "20.120.45.67"),
    },
    "gcp": {
        "region": "us-central1",
        "health": "https://app-gcp.example.com/health",
        "ip": os.getenv("GCP_LB_IP", "34.120.78.90"),
    },
}
ZONE_ID = os.getenv("ROUTE53_ZONE_ID", "Z1234567890")
RECORD = "app.example.com"
DD_KEY = os.getenv("DATADOG_API_KEY", "")
SLACK_HOOK = os.getenv("SLACK_WEBHOOK_URL", "")


def check_health(cloud: str) -> bool:
    try:
        r = requests.get(CLOUDS[cloud]["health"], timeout=10)
        ok = r.status_code == 200 and r.json().get("status") == "healthy"
        logger.info(f"  {cloud} health: {'PASS' if ok else 'FAIL'}")
        return ok
    except Exception as e:
        logger.error(f"  {cloud} health failed: {e}")
        return False


def promote_database(cloud: str):
    logger.info(f"Promoting database replica on {cloud}...")
    if cloud == "azure":
        os.system(
            "az postgres flexible-server replica stop-replication"
            " --name ecommerce-db-azure --resource-group prod-rg"
        )
    elif cloud == "gcp":
        os.system("gcloud sql instances promote-replica ecommerce-db-gcp --quiet")


def update_dns(target: str):
    r53 = boto3.client("route53")
    cfg = CLOUDS[target]
    if target == "aws":
        record = {
            "Type": "A",
            "Name": RECORD,
            "AliasTarget": {
                "DNSName": cfg["alb_dns"],
                "HostedZoneId": cfg["alb_zone"],
                "EvaluateTargetHealth": True,
            },
        }
    else:
        record = {
            "Type": "A",
            "Name": RECORD,
            "TTL": 60,
            "ResourceRecords": [{"Value": cfg["ip"]}],
        }

    logger.info(f"Updating DNS: {RECORD} → {target}")
    r53.change_resource_record_sets(
        HostedZoneId=ZONE_ID,
        ChangeBatch={
            "Comment": f"DR failover to {target}",
            "Changes": [{"Action": "UPSERT", "ResourceRecordSet": record}],
        },
    )


def verify(target: str, retries=12, interval=10) -> bool:
    url = f"https://{RECORD}/health"
    for i in range(1, retries + 1):
        try:
            if requests.get(url, timeout=10).status_code == 200:
                logger.info(f"  Verified on attempt {i}")
                return True
        except Exception:
            pass
        logger.info(f"  Attempt {i}/{retries}, waiting {interval}s...")
        time.sleep(interval)
    return False


def notify(target: str, reason: str, ok: bool):
    status = "SUCCESS" if ok else "FAILED"
    ts = datetime.now(timezone.utc).isoformat()
    if DD_KEY:
        requests.post(
            "https://api.datadoghq.com/api/v1/events",
            headers={"DD-API-KEY": DD_KEY},
            json={
                "title": f"DR Failover {status}: → {target}",
                "text": f"Reason: {reason}\nTime: {ts}",
                "alert_type": "success" if ok else "error",
                "tags": [f"cloud:{target}", "type:dr-failover"],
            },
        )
    if SLACK_HOOK:
        emoji = ":white_check_mark:" if ok else ":x:"
        requests.post(
            SLACK_HOOK,
            json={"text": f"{emoji} *DR {status}* → `{target}` | {reason} | {ts}"},
        )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True, choices=["aws", "azure", "gcp"])
    p.add_argument("--reason", required=True)
    p.add_argument("--skip-db", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    logger.info(
        f"{'='*60}\nDR FAILOVER → {args.target.upper()}\n"
        f"Reason: {args.reason}\n{'='*60}"
    )

    logger.info("[1/5] Checking health...")
    if not check_health(args.target):
        logger.error("Target unhealthy. Aborting.")
        notify(args.target, args.reason, False)
        sys.exit(1)

    if args.dry_run:
        logger.info("[DRY RUN] Checks passed. No changes.")
        return

    if not args.skip_db:
        logger.info("[2/5] Promoting database...")
        promote_database(args.target)
    logger.info("[3/5] Updating DNS...")
    update_dns(args.target)
    logger.info("[4/5] Verifying...")
    ok = verify(args.target)
    logger.info("[5/5] Notifying...")
    notify(args.target, args.reason, ok)

    if ok:
        logger.info("\n✓ Failover complete.")
    else:
        logger.error("\n✗ Verification failed. Manual intervention required.")
        sys.exit(1)


if __name__ == "__main__":
    main()
