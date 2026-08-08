import io
import json
import os
import subprocess
import sys
import time
import requests
from dotenv import load_dotenv

PERSISTENCE_FILE = ".messages.json"


if os.name == "nt":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RESET = "\033[0m"

load_dotenv()
API_KEY = os.environ["API_KEY"]
API_URL = os.environ["API_BASE_URL"]
MODEL = os.environ["MODEL"]

SYSTEM_PROMPT = """You are an autonomous AI software engineering agent running directly in the user's terminal.

# CAPABILITIES & TOOLS
- You can execute shell commands using `execute_cmd`.
- You can read file contents (and specific line ranges) using `read_file`.
- You can write or modify file contents using `write_file`.

# OPERATIONAL MODES
- **build mode**: Tools are fully active. Execute commands and inspect or modify files as needed.
- **plan mode**: Tools are disabled. Formulate strategies, discuss architecture, and plan with the user.

# CORE RULES
1. **READ BEFORE WRITE**: If a file already exists, you MUST use `read_file` on it before using `write_file`. The system will reject writes to unread existing files. New non-existent files can be created directly.
2. **FILE WRITING & PARTIAL EDITS**: `write_file` supports full writes or line-based partial edits. For partial edits, specify `old_content` matching the target lines exactly. If `old_content` does not match the file content exactly, the write operation will fail and return feedback.
3. **VERIFY CHANGES**: After modifying code in build mode, run shell commands (`execute_cmd`) to verify and test your changes.
4. **CROSS-PLATFORM**: Adapt your shell commands to the host operating system."""

if os.path.exists("AGENTS.md"):
    with open("AGENTS.md", "r", encoding="utf-8") as f:
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
            "description": "Write or update file content. Pass old_content for exact line-based partial replacements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "old_content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


def save_messages(messages):
    try:
        with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
    except Exception:
        pass


def load_messages():
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def call_model(messages, mode="build", retries=3, backoff_factor=1):
    active_tools = TOOLS if mode == "build" else []
    for attempt in range(retries):
        try:
            response = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": MODEL,
                    "messages": messages,
                    "tools": active_tools,
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


def write_file(path, content, files_read, old_content=None):
    if os.path.exists(path) and path not in files_read:
        return f"Action denied: read '{path}' before writing to it"
    try:
        if old_content:
            if not os.path.exists(path):
                return f"Write failed: '{path}' does not exist"
            with open(path, "r", encoding="utf-8") as f:
                file_text = f.read()
            if old_content not in file_text:
                return "Write failed: target content did not match file content exactly"
            if file_text.count(old_content) > 1:
                return f"Write failed: target content matched multiple locations in '{path}'"
            file_text = file_text.replace(old_content, content, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(file_text)
            files_read.add(path)
            return f"Successfully updated '{path}'"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        files_read.add(path)
        return f"Successfully wrote to '{path}'"
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
            print(f"{YELLOW}[Executing command]: {cmd}{RESET}")
            output = execute_cmd(cmd)
        elif name == "read_file":
            path = args.get("path", "")
            print(f"{YELLOW}[Reading file]: {path}{RESET}")
            output = read_file(
                path,
                args.get("start_line"),
                args.get("end_line"),
                files_read,
            )
        elif name == "write_file":
            path = args.get("path", "")
            print(f"{YELLOW}[Writing file]: {path}{RESET}")
            output = write_file(
                path,
                args.get("content", ""),
                files_read,
                args.get("old_content"),
            )
        else:
            output = f"Unknown tool: {name}"

        lines = output.splitlines()
        if len(lines) > 5:
            display_output = "\n".join(lines[:5]) + "\n... [truncated for display]"
        else:
            display_output = output

        if display_output:
            print(f"{YELLOW}Output:\n{display_output}{RESET}")

        messages.append(
            {
                "role": "tool",
                "tool_call_id": call["id"],
                "content": output,
            }
        )


def main():
    files_read = set()
    mode = "build"

    messages = load_messages()
    if not messages:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        save_messages(messages)
    else:
        print(
            f"{YELLOW}[Restored previous session history from {PERSISTENCE_FILE}]{RESET}"
        )

    while True:
        approx_tokens = sum(len(str(m)) for m in messages) // 4
        print(f"{YELLOW}[Status | Mode: {mode} | Tokens: ~{approx_tokens}]{RESET}")

        try:
            user_input = input(f"{GREEN}You: {RESET}").strip()
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[Exiting...]{RESET}")
            break

        if user_input == "/exit":
            break

        if user_input == "/clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            files_read.clear()
            save_messages(messages)
            print(f"{YELLOW}[Context cleared]{RESET}")
            continue

        if user_input in ("/plan", "/build"):
            mode = user_input[1:]
            messages.append(
                {
                    "role": "user",
                    "content": f"[System Note: User switched mode to '{mode}']",
                }
            )
            save_messages(messages)
            print(f"{YELLOW}[Mode set to: {mode}]{RESET}")
            continue

        messages.append({"role": "user", "content": user_input})
        save_messages(messages)

        try:
            while True:
                reply = call_model(messages, mode=mode)

                if reply.get("content"):
                    print(f"{BLUE}Agent: {reply['content']}{RESET}")

                messages.append(reply)
                save_messages(messages)

                tool_calls = reply.get("tool_calls")
                if not tool_calls:
                    break

                if mode == "plan":
                    for call in tool_calls:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": "Action denied: Tool execution is disabled in plan mode. Tell the user to switch to build mode using /build.",
                            }
                        )
                    save_messages(messages)
                    print(
                        f"{YELLOW}[Action denied: Tool execution restricted in plan mode]{RESET}"
                    )
                    break

                handle_toolcall(tool_calls, messages, files_read)
                save_messages(messages)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}[Response forcefully stopped]{RESET}")
            messages.append(
                {
                    "role": "user",
                    "content": "[System Note: User forcefully stopped the agent response]",
                }
            )
            save_messages(messages)
        except Exception as e:
            print(f"\n{YELLOW}[Error: {e}]{RESET}")
            messages.append(
                {
                    "role": "user",
                    "content": f"[System Note: Agent response failed with error: {e}]",
                }
            )
            save_messages(messages)


if __name__ == "__main__":
    main()
