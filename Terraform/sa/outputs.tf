output "ai_agent_service_account_email" {

  description = "Email of AI Agent service account"

  value = google_service_account.ai_agent.email

}