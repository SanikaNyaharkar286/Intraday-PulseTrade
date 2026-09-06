variable "project_id" {
  description = "GCP project ID for PulseTrade"
  type        = string
}

variable "region" {
  description = "Default region"
  type        = string
  default     = "us-east1"
}

variable "service_account_id" {
  description = "Service account ID (becomes part of the email)"
  type        = string
  default     = "pulse-trade-agent"
}

variable "service_account_display_name" {
  description = "Human-readable name for the service account"
  type        = string
  default     = "PulseTrade AI Agent Service Account"
}

variable "enable_apis" {
  description = "APIs required for the agent to run"
  type        = list(string)
  default = [
    "iam.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
  ]
}

variable "bq_read_datasets" {
  description = "BigQuery datasets the agent gets dataViewer on (least privilege — not Gold/Silver/Bronze)"
  type        = list(string)
  default     = ["pulse_trade_semantic", "pulse_trade_ai"]
}

variable "create_local_key" {
  description = "Whether to generate a local JSON key for laptop/VS Code testing. Set false once Cloud Run deployment uses the SA directly."
  type        = bool
  default     = true
}