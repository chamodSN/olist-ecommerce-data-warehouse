variable "aws_region" {
  type        = string
  description = "The region for all aws resources"
  default     = "ap-southeast-2"
}

variable "project_name"{
  type        = string
  description = "Prefix used for naming all resources"
  default     = "olist-ecommerce-dw"
}

variable "project_owner"{
  type        = string
  description = "My name to keep the bucket unique globally"
  default     = "csn"
}

variable "project_version"{
  type        = string
  description = "Project stage like dev/prod/QA"
  default     = "dev"
}

variable "redshift_admin_password"{
  type        = string
  description = "Admin password for redshift serverless namespace"
  sensitive   = true
}