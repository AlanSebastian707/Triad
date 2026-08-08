import os
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.environ["API_KEY"]
API_URL = os.environ["API_BASE_URL"]
MODEL = os.environ["MODEL"]
response = requests.post(
    API_URL,
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say hi in 5 words."}],
    },
)
print(response.json()["choices"][0]["message"]["content"])