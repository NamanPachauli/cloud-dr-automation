
import json
import os
from datetime import datetime, timezone
from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, jsonify, request
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "cloud-dr-backups")
ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
)

REQUEST_COUNT = Counter(
    "cloud_dr_requests_total",
    "Total requests handled by the Cloud DR application",
    ["endpoint", "method"],
)


@app.before_request
def count_request():
    REQUEST_COUNT.labels(
        endpoint=request.path,
        method=request.method,
    ).inc()


@app.get("/")
def home():
    return jsonify({
        "project": "Cloud Infrastructure Automation & Disaster Recovery Platform",
        "environment": "LocalStack simulation",
        "endpoints": [
            "/health",
            "/backup",
            "/backups",
            "/restore",
            "/metrics",
        ],
    })


@app.get("/health")
def health():
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        return jsonify({
            "status": "healthy",
            "s3_bucket": BUCKET_NAME,
            "environment": "LocalStack",
        }), 200
    except (BotoCoreError, ClientError) as exc:
        return jsonify({
            "status": "unhealthy",
            "reason": str(exc),
        }), 503


@app.post("/backup")
def create_backup():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Send a JSON object in the request body"}), 400

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"backups/backup-{timestamp}.json"

    backup_document = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": payload,
    }

    try:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(backup_document, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        return jsonify({
            "status": "backup_created",
            "bucket": BUCKET_NAME,
            "key": key,
        }), 201
    except (BotoCoreError, ClientError) as exc:
        return jsonify({"error": str(exc)}), 503


@app.get("/backups")
def list_backups():
    try:
        result = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="backups/")
        backups = [
            {
                "key": item["Key"],
                "size_bytes": item["Size"],
                "last_modified": item["LastModified"].isoformat(),
            }
            for item in result.get("Contents", [])
        ]
        return jsonify({"count": len(backups), "backups": backups}), 200
    except (BotoCoreError, ClientError) as exc:
        return jsonify({"error": str(exc)}), 503


@app.post("/restore")
def restore_backup():
    body = request.get_json(silent=True) or {}
    key = body.get("key")

    if not isinstance(key, str) or not key.startswith("backups/"):
        return jsonify({
            "error": "Provide a valid backup key beginning with backups/"
        }), 400

    try:
        result = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        document = json.loads(result["Body"].read().decode("utf-8"))
        return jsonify({
            "status": "restore_read_success",
            "key": key,
            "restored_data": document.get("data"),
        }), 200
    except (BotoCoreError, ClientError, json.JSONDecodeError) as exc:
        return jsonify({"error": str(exc)}), 404


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
