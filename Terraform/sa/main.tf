resource "google_service_account" "ai_agent" {

  account_id = var.service_account_name


  display_name = "PulseTrade AI Agent Service Account"


  description = "Used by ADK agent to access AI semantic BigQuery dataset"

}

resource "google_project_iam_member" "ai_agent_job_user" {


  project = var.project_id


  role = "roles/bigquery.jobUser"


  member = "serviceAccount:${google_service_account.ai_agent.email}"

}

resource "google_bigquery_dataset_iam_member" "ai_agent_data_viewer" {


  dataset_id = var.ai_dataset_id


  role = "roles/bigquery.dataViewer"


  member = "serviceAccount:${google_service_account.ai_agent.email}"

}