"""Simple web app deployed identically across AWS, Azure, and GCP."""
import os, socket
from fastapi import FastAPI

app = FastAPI(title="Multi-Cloud App")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "cloud": os.getenv("CLOUD_PROVIDER", "unknown"),
        "region": os.getenv("CLOUD_REGION", "unknown"),
        "hostname": socket.gethostname(),
    }

@app.get("/")
async def root():
    return {"message": "Multi-cloud app", "cloud": os.getenv("CLOUD_PROVIDER", "unknown")}
