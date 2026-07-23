resource "aws_redshiftserverless_namespace" "olist_dw" {
  namespace_name = "${var.project_name}-${var.project_owner}-${var.project_version}-ns"
  admin_username       = "admin"
  admin_user_password  = var.redshift_admin_password
  db_name              = "olist_dw"
}