
import json
import os
import boto3
from botocore.exceptions import ClientError

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "cloud-dr-backups")
BACKUP_KEY = os.getenv("BACKUP_KEY", "dr-test/backup-test.json")

def lambda_handler(event, context):
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    )

    try:
        response = s3.head_object(
            Bucket=BUCKET_NAME,
            Key=BACKUP_KEY
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "backup_verified",
                "bucket": BUCKET_NAME,
                "key": BACKUP_KEY,
                "size_bytes": response["ContentLength"]
            })
        }

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")

        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "backup_verification_failed",
                "error": error_code,
                "bucket": BUCKET_NAME,
                "key": BACKUP_KEY
            })
        }
