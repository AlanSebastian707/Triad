import io
import json
import os
import subprocess
import sys
import time
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

if os.path.exists("Agents.md"):
    with open("Agents.md", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT += "\n\nProject Context and Skills:\n" + f.read()

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
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, overwriting its contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


def call_model(messages, retries=3, backoff_factor=1):
    for attempt in range(retries):
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": MODEL,
                    "messages": messages,
                    "tools": TOOLS,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except (
            requests.RequestException,
            json.JSONDecodeError,
            KeyError,
            IndexError,
        ) as e:
            if attempt == retries - 1:
                raise e
            time.sleep(backoff_factor * (2**attempt))


def execute_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def read_file(path, start_line=None, end_line=None, files_read=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if files_read is not None:
            files_read.add(path)

        start = max(0, start_line - 1) if start_line is not None else 0
        end = end_line if end_line is not None else len(lines)

        return "".join(lines[start:end])
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


def write_file(path, content, files_read):
    if os.path.exists(path) and path not in files_read:
        return f"Action denied: read '{path}' before writing to it"
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        files_read.add(path)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file '{path}': {str(e)}"


def handle_toolcall(tool_calls, messages, files_read):
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
            cmd = args.get("command", "")
            print(f"[Executing command]: {cmd}")
            output = execute_cmd(cmd)
        elif name == "read_file":
            path = args.get("path", "")
            print(f"[Reading file]: {path}")
            output = read_file(
                path,
                args.get("start_line"),
                args.get("end_line"),
                files_read,
            )
        elif name == "write_file":
            path = args.get("path", "")
            print(f"[Writing file]: {path}")
            output = write_file(path, args.get("content", ""), files_read)
        else:
            output = f"Unknown tool: {name}"

        lines = output.splitlines()
        if len(lines) > 5:
            display_output = "\n".join(lines[:5]) + "\n... [truncated for display]"
        else:
            display_output = output

        if display_output:
            print("Output:", display_output)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": call["id"],
                "content": output,
            }
        )


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    files_read = set()

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

            handle_toolcall(tool_calls, messages, files_read)


if __name__ == "__main__":
    main()
