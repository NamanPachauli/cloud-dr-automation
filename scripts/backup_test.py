
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BUCKET = "cloud-dr-backups"
OBJECT_KEY = (
    "dr-test/backup-test-"
    + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    + ".json"
)

def run(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=20
    )

def main():
    payload = {
        "project": "cloud-dr-automation",
        "test": "disaster-recovery-backup",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "test-backup"
    }

    temp_file = Path("reports") / "backup-test.json"
    temp_file.parent.mkdir(exist_ok=True)
    temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    check = run([
        "docker", "compose", "exec", "-T", "localstack",
        "awslocal", "s3api", "head-bucket", "--bucket", BUCKET
    ])

    if check.returncode != 0:
        print(f"FAIL: Bucket '{BUCKET}' is unavailable.")
        print(check.stderr.strip() or check.stdout.strip())
        sys.exit(1)

    upload = run([
        "docker", "compose", "exec", "-T", "localstack",
        "awslocal", "s3", "cp", "-", f"s3://{BUCKET}/{OBJECT_KEY}"
    ])

    # The AWS CLI cp command needs a file path, so use a second command
    # to copy the generated local file into the LocalStack container.
    copy_file = run([
        "docker", "compose", "cp",
        str(temp_file), "localstack:/tmp/backup-test.json"
    ])
    if copy_file.returncode != 0:
        print("FAIL: Could not copy the test file into LocalStack.")
        print(copy_file.stderr.strip())
        sys.exit(1)

    upload = run([
        "docker", "compose", "exec", "-T", "localstack",
        "awslocal", "s3", "cp", "/tmp/backup-test.json",
        f"s3://{BUCKET}/{OBJECT_KEY}"
    ])

    if upload.returncode != 0:
        print("FAIL: Backup upload failed.")
        print(upload.stderr.strip())
        sys.exit(1)

    verify = run([
        "docker", "compose", "exec", "-T", "localstack",
        "awslocal", "s3api", "head-object",
        "--bucket", BUCKET, "--key", OBJECT_KEY
    ])

    if verify.returncode != 0:
        print("FAIL: Uploaded backup could not be verified.")
        print(verify.stderr.strip())
        sys.exit(1)

    print("PASS: S3 bucket is accessible.")
    print(f"PASS: Backup uploaded and verified: {OBJECT_KEY}")
    print(f"Evidence file: {temp_file}")
    print("NOTE: This is a LocalStack simulation, not real AWS.")

if __name__ == "__main__":
    main()

