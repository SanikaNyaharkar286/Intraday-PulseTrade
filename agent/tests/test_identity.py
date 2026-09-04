import google.auth

credentials, project = google.auth.default()

print("Project:", project)

print("Credentials type:")
print(type(credentials))

if hasattr(credentials, "service_account_email"):
    print("Service Account:")
    print(credentials.service_account_email)
else:
    print("Not using service account credentials")