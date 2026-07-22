resource "aws_s3_bucket" "bronze"{
    bucket = "${var.project_name}-${var.project_owner}-${var.project_version}-bronze"

    tags = {
        Provider = var.project_name
        Layer = "bronze"
    }
}

resource "aws_s3_bucket" "silver"{
    bucket = "${var.project_name}-${var.project_owner}-${var.project_version}-silver"

    tags = {
        Provider = var.project_name
        Layer = "silver"
    }
}

resource "aws_s3_bucket" "gold"{
    bucket = "${var.project_name}-${var.project_owner}-${var.project_version}-gold"

    tags = {
        Provider = var.project_name
        Layer = "gold"
    }
}

# access using local terraform identifider

resource "aws_s3_bucket_public_access_block" "bronze" {
    bucket  =   aws_s3_bucket.bronze.id 
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "silver" {
    bucket  =   aws_s3_bucket.silver.id
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "gold" {
    bucket  =   aws_s3_bucket.gold.id
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

# Versioning on bronze

resource "aws_s3_bucket_versioning" "bronze_versioning" {
  bucket = aws_s3_bucket.bronze.id
  versioning_configuration {
    status = "Enabled"
  }
}