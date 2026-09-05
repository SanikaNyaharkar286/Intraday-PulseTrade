import os
from dotenv import load_dotenv


load_dotenv()


PROJECT_ID = os.getenv(
    "GCP_PROJECT_ID"
)

AI_DATASET = os.getenv(
    "BQ_AI_SEMANTIC_DATASET"
)

BQ_LOCATION = os.getenv(
    "BQ_LOCATION",
    "US"
)