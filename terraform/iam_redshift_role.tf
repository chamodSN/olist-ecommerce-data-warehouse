data "aws_iam_policy_document" "redshift_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "redshift_s3_role" {
  name               = "${var.project_name}-${var.project_owner}-${var.project_version}-redshift-s3-role"
  assume_role_policy = data.aws_iam_policy_document.redshift_assume_role.json

  tags = {
    Project = var.project_name
  }
}

data "aws_iam_policy_document" "redshift_s3_access" {
  statement {
    sid    = "AllowListProjectBuckets"
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
    sid    = "AllowReadWriteObjectsInProjectBuckets"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.bronze.arn}/*",
      "${aws_s3_bucket.silver.arn}/*",
      "${aws_s3_bucket.gold.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "redshift_s3_access" {
  name        = "${var.project_name}-${var.project_owner}-${var.project_version}-redshift-s3-policy"
  description = "Scoped S3 access for Redshift Serverless to read Bronze/Silver and read/write Gold"
  policy      = data.aws_iam_policy_document.redshift_s3_access.json
}

resource "aws_iam_role_policy_attachment" "redshift_s3_attach" {
  role       = aws_iam_role.redshift_s3_role.name
  policy_arn = aws_iam_policy.redshift_s3_access.arn
}