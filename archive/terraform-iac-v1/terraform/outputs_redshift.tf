output "redshift_workgroup_endpoint" {
  value = aws_redshiftserverless_workgroup.olist_dw.endpoint
}

output "redshift_namespace_name" {
  value = aws_redshiftserverless_namespace.olist_dw.namespace_name
}