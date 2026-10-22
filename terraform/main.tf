
resource "aws_s3_bucket" "backups" {
  bucket = "cloud-dr-backups"

  tags = {
    Project     = "cloud-dr-automation"
    Environment = "local-lab"
    Purpose     = "disaster-recovery-backups"
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  bucket = aws_s3_bucket.backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "backup_bucket_name" {
  description = "S3 bucket provisioned by Terraform in LocalStack"
  value       = aws_s3_bucket.backups.bucket
}
