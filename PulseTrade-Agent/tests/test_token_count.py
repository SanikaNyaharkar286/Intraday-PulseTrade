from google import genai
from google.genai.types import HttpOptions

from agent.instructions import INSTRUCTIONS


client = genai.Client(
    vertexai=True,
    project="project-001658fa-3ce5-4746-980",
    location="us-central1",
    http_options=HttpOptions(
        api_version="v1"
    )
)


response = client.models.count_tokens(
    model="gemini-2.5-flash",
    contents=INSTRUCTIONS
)


print("Tokens:", response.total_tokens)
print("Characters:", len(INSTRUCTIONS))