import os
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference

load_dotenv()

API_KEY = os.getenv("WATSONX_API_KEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
REGION = os.getenv("WATSONX_REGION")
URL = "https://us-south.ml.cloud.ibm.com"

# Initialize model
model = ModelInference(
    model_id="ibm/granite-3-3-8b-instruct",  # Production-ready alternative
    credentials={
        "api_key": API_KEY,
        "url": URL
    },
    project_id=PROJECT_ID,
)

def classify_resume(text: str) -> str:
    with open("prompts/job_classifier_prompt.txt") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(resume_text=text)
    response = model.generate(prompt=prompt)
    return response['results'][0]['generated_text'].strip()
