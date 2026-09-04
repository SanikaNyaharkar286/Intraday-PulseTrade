variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region used by the Google provider"
  type        = string
  default     = "asia-south1"
}

variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "asia-south1"
}

variable "bronze_dataset" {
  description = "Bronze BigQuery dataset name"
  type        = string
  default     = "bronze_dataset"
}

variable "bronze_table" {
  description = "Bronze BigQuery table name"
  type        = string
  default     = "intraday_master"
}

variable "audit_dataset" {
  description = "Audit BigQuery dataset name"
  type        = string
  default     = "audit_dataset"
}

variable "audit_table" {
  description = "Audit BigQuery table name"
  type        = string
  default     = "pipeline_audit"
}

variable "deletion_protection" {
  description = "Enable BigQuery table deletion protection"
  type        = bool
  default     = false
}
