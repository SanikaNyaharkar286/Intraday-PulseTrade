resource "google_project_service" "required" {
  for_each = toset(var.enable_apis)
  project  = var.project_id
  service  = each.value

  disable_on_destroy = false
}

resource "google_service_account" "pulse_trade_agent" {
  account_id   = var.service_account_id
  display_name = var.service_account_display_name
  project      = var.project_id

  depends_on = [google_project_service.required]
}

# Local-dev-only key — for running the ADK agent from your machine.
# Set create_local_key = false once Cloud Run runs the agent with this SA natively.
resource "google_service_account_key" "pulse_trade_agent_key" {
  count               = var.create_local_key ? 1 : 0
  service_account_id  = google_service_account.pulse_trade_agent.name
}

resource "local_file" "pulse_trade_agent_key_file" {
  count           = var.create_local_key ? 1 : 0
  content         = base64decode(google_service_account_key.pulse_trade_agent_key[0].private_key)
  filename        = "${path.module}/${var.service_account_id}-key.json"
  file_permission = "0600"
}

# Lets the agent create/run BigQuery query jobs (project-scoped — this isn't dataset-specific)
resource "google_project_iam_member" "bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pulse_trade_agent.email}"
}

# Lets the agent call Gemini via Vertex AI
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.pulse_trade_agent.email}"
}

# Dataset-scoped read access — ONLY the semantic + AI snapshot datasets.
# No project-level dataViewer grant, so Gold/Silver/Bronze stay off-limits.
resource "google_bigquery_dataset_iam_member" "read_access" {
  for_each   = toset(var.bq_read_datasets)
  project    = var.project_id
  dataset_id = each.value
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.pulse_trade_agent.email}"
}