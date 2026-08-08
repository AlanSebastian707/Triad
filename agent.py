import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["API_KEY"]
API_URL = os.environ["API_BASE_URL"]
MODEL = os.environ["MODEL"]

SYSTEM_PROMPT = "You are a terminal coding agent. Always identify yourself as a coding agent running in the terminal."

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_input = input("You: ")

    messages.append({"role": "user", "content": user_input})

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": messages,
        },
    )

    reply = response.json()["choices"][0]["message"]
    print("Agent:", reply["content"])

    messages.append(reply)
