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

data "aws_iam_policy_document" "redshift_glue_access" {
  statement {
    sid    = "AllowGlueCatalogAccess"
    effect = "Allow"
    actions = [
      "glue:CreateDatabase",
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:CreateTable",
      "glue:GetTable",
      "glue:GetTables",
      "glue:UpdateTable",
      "glue:DeleteTable",
      "glue:BatchCreatePartition",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:BatchGetPartition",
    ]

    resources = [
      "arn:aws:glue:${var.aws_region}:*:catalog",
      "arn:aws:glue:${var.aws_region}:*:database/olist_silver",
      "arn:aws:glue:${var.aws_region}:*:table/olist_silver/*",
    ]
  }
}

resource "aws_iam_policy" "redshift_glue_access" {
  name        = "${var.project_name}-${var.project_owner}-${var.project_version}-redshift-glue-policy"
  description = "Allows Redshift Spectrum to read/write the olist_silver Glue Catalog database"
  policy      = data.aws_iam_policy_document.redshift_glue_access.json
}

resource "aws_iam_role_policy_attachment" "redshift_glue_attach" {
  role       = aws_iam_role.redshift_s3_role.name
  policy_arn = aws_iam_policy.redshift_glue_access.arn
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