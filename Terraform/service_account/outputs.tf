output "service_account_email" {
  description = "Email address of the migration service account"

  value = google_service_account.migration.email
}