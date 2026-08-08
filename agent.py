import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["API_KEY"]
API_URL = os.environ["API_BASE_URL"]
MODEL = os.environ["MODEL"]

SYSTEM_PROMPT = (
    "You are a terminal coding assistant. always identify as the  a coding agent."
)

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Who are you?"},
]

response = requests.post(
    API_URL,
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": MODEL,
        "messages": messages,
    },
)

reply = response.json()["choices"][0]["message"]
print(reply["content"])

messages.append(reply)
