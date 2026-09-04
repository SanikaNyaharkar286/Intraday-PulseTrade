import os
from dotenv import load_dotenv


load_dotenv()


PROJECT_ID = os.getenv(
    "GOOGLE_CLOUD_PROJECT"
)


BIGQUERY_DATASET = os.getenv(
    "BIGQUERY_DATASET"
)


BIGQUERY_LOCATION = os.getenv(
    "BIGQUERY_LOCATION",
    "asia-south1"
)


MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemini-2.5-flash"
)