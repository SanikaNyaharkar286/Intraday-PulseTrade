output "service_account_email" {
  description = "Email of the agent's service account — use as Cloud Run runtime SA later"
  value       = google_service_account.pulse_trade_agent.email
}

output "key_file_path" {
  description = "Path to the local JSON key, if created"
  value       = var.create_local_key ? local_file.pulse_trade_agent_key_file[0].filename : null
  sensitive   = true
}