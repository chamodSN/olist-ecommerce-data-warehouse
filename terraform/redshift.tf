#Namespace
resource "aws_redshiftserverless_namespace" "olist_dw" {
  namespace_name = "${var.project_name}-${var.project_owner}-${var.project_version}-ns"
  admin_username       = "admin"
  admin_user_password  = var.redshift_admin_password
  db_name              = "olist_dw"

  iam_roles = [aws_iam_role.redshift_s3_role.arn]

  default_iam_role_arn = aws_iam_role.redshift_s3_role.arn

  tags = {
    Project = var.project_name
    Layer   = "warehouse"
  }
}


#Workgroup
resource "aws_redshiftserverless_workgroup" "olist_dw"{
    namespace_name = aws_redshiftserverless_namespace.olist_dw.namespace_name
    workgroup_name = "${var.project_name}-${var.project_owner}-${var.project_version}-wg"

    base_capacity = 8

    publicly_accessible = true

    tags = {
        Project = var.project_name
        Layer   = "warehouse"
    }
}