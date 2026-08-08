import io
import json
import os
import subprocess
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

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_cmd",
            "description": "Run a shell command and return its output",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file, optionally specifying start and end lines",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
    },
]


def call_model(messages):
    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
        },
    )
    return response.json()["choices"][0]["message"]


def execute_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def read_file(path, start_line=None, end_line=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start = max(0, start_line - 1) if start_line is not None else 0
        end = end_line if end_line is not None else len(lines)

        return "".join(lines[start:end])
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


def handle_toolcall(tool_calls, messages):
    for call in tool_calls:
        name = call["function"]["name"]
        try:
            args = json.loads(call["function"]["arguments"])
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": f"Error: invalid JSON arguments for '{name}' ({e}). Respond again with valid JSON.",
                }
            )
            continue

        if name == "execute_cmd":
            output = execute_cmd(args["command"])
            print("[execute_cmd]", output)
        elif name == "read_file":
            output = read_file(
                args["path"],
                args.get("start_line"),
                args.get("end_line"),
            )
            print(f"[read_file {args['path']}]", output)
        else:
            output = f"Unknown tool: {name}"

        messages.append(
            {
                "role": "tool",
                "tool_call_id": call["id"],
                "content": output,
            }
        )


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ")

        messages.append({"role": "user", "content": user_input})

        while True:
            reply = call_model(messages)

            if reply.get("content"):
                print("Agent:", reply["content"])

            messages.append(reply)

            tool_calls = reply.get("tool_calls")
            if not tool_calls:
                break

            handle_toolcall(tool_calls, messages)


if __name__ == "__main__":
    main()
