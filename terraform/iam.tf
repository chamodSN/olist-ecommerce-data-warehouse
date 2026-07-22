# The IAM user itself
resource "aws_iam_user" "olist_dw_dev" {
  name = "olist-dw-dev"

  tags = {
    Project = var.project_name
  }
}

# Programmatic access key for this user
resource "aws_iam_access_key" "olist_dw_dev_key" {
  user = aws_iam_user.olist_dw_dev.name
}

# The scoped policy, built directly from actual bucket resources

data "aws_iam_policy_document" "olist_dw_s3_scoped" {
  statement {
    sid    = "AllowListSpecificBuckets"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      aws_s3_bucket.bronze.arn,
      aws_s3_bucket.silver.arn,
      aws_s3_bucket.gold.arn,
    ]
  }

  statement {
    sid    = "AllowObjectReadWriteInProjectBuckets"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.bronze.arn}/*",
      "${aws_s3_bucket.silver.arn}/*",
      "${aws_s3_bucket.gold.arn}/*",
    ]
  }

  statement {
    sid    = "AllowObjectVersioningOnBronze"
    effect = "Allow"
    actions = [
      "s3:GetObjectVersion",
      "s3:ListBucketVersions",
    ]
    resources = [
      aws_s3_bucket.bronze.arn,
      "${aws_s3_bucket.bronze.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "olist_dw_s3_scoped" {
  name        = "olist-dw-s3-scoped-policy"
  description = "Least-privilege S3 access scoped to the olist-dw bronze/silver/gold buckets only"
  policy      = data.aws_iam_policy_document.olist_dw_s3_scoped.json
}

resource "aws_iam_user_policy_attachment" "attach_scoped_policy" {
  user       = aws_iam_user.olist_dw_dev.name
  policy_arn = aws_iam_policy.olist_dw_s3_scoped.arn
}