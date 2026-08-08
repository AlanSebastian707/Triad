import io
import os
import sys
import requests
from dotenv import load_dotenv

if os.name == "nt":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
API_KEY = os.environ["API_KEY"]
API_URL = os.environ["API_BASE_URL"]
MODEL = os.environ["MODEL"]

SYSTEM_PROMPT = "You are a terminal coding agent. Always identify yourself as a coding agent running in the terminal."


def call_model(messages):
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": messages,
        },
    )
    return response.json()["choices"][0]["message"]


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ")

        messages.append({"role": "user", "content": user_input})

        reply = call_model(messages)
        print("Agent:", reply["content"])

        messages.append(reply)


if __name__ == "__main__":
    main()
