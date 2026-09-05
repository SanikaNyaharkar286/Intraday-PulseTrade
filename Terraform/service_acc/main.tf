resource "google_service_account" "agent" {

  account_id = var.service_account_name

  display_name = var.display_name

}


resource "google_project_iam_member" "bigquery_job_user" {

  project = var.project_id

  role = "roles/bigquery.jobUser"

  member = "serviceAccount:${google_service_account.agent.email}"

}


resource "google_bigquery_dataset_iam_member" "dataset_access" {

  for_each = toset(var.allowed_datasets)

  dataset_id = each.value

  role = "roles/bigquery.dataViewer"

  member = "serviceAccount:${google_service_account.agent.email}"

}