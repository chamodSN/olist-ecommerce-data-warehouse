output "iam_user_name" {
  value = aws_iam_user.olist_dw_dev.name
}

# Marked sensitive so it doesn't print in plain text in terraform plan/apply logs
output "access_key_id" {
  value     = aws_iam_access_key.olist_dw_dev_key.id
  sensitive = true
}

output "secret_access_key" {
  value     = aws_iam_access_key.olist_dw_dev_key.secret
  sensitive = true
}