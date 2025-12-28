#!/usr/bin/env python3
"""tell: Convert natural language to shell commands and confirm before execution."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Optional, Tuple, List, Dict

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

# --- NEW IMPORTS ---
from tell.utils import load_history, save_history, clear_history

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # type: ignore[assignment]

try:
    from groq import Groq
except Exception:
    Groq = None  # type: ignore[assignment]

app = typer.Typer(add_completion=False, help="Convert natural language to commands via Groq.")
console = Console()

if load_dotenv:
    load_dotenv()


def detect_os() -> str:
    system = platform.system().lower()
    if system.startswith("linux"):
        return "Linux"
    console.print("[red]This tool currently supports Linux only.[/red]")
    raise typer.Exit(code=1)


def detect_shell() -> Tuple[str, str]:
    shell_path = os.environ.get("SHELL", "/bin/bash")
    return os.path.basename(shell_path).lower(), shell_path


def get_directory_context(max_files: int = 50) -> str:
    """Returns a comma-separated list of filenames in the current directory."""
    try:
        files = [f for f in os.listdir(".") if not f.startswith(".")]
        files.sort()
        if len(files) > max_files:
            return ", ".join(files[:max_files]) + f", ... (+{len(files) - max_files} more)"
        if not files:
            return "(Empty Directory)"
        return ", ".join(files)
    except Exception:
        return "(Could not read directory)"


def build_system_prompt(os_name: str, shell_name: str, file_context: str) -> str:
    return (
        "You are a command generator for Linux. Return ONLY the raw command string; "
        "no markdown, no backticks, no explanations. "
        f"Target OS: {os_name}. Shell: {shell_name}. "
        f"The user is currently in a directory containing these files: [{file_context}]. "
        "Use this context to resolve vague requests (e.g., 'make it recursive' refers to previous command)."
    )


def strip_command(command: str) -> str:
    cleaned = command.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(cleaned.split("\n")[1:])
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip().strip("`")


def syntax_lexer(shell_name: str) -> str:
    if shell_name == "zsh":
        return "zsh"
    return "bash"


def ensure_groq() -> Groq:
    if Groq is None:
        console.print(
            "[red]Missing dependency:[/red] groq. Install with `pip install -r requirements.txt`."
        )
        raise typer.Exit(code=1)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        console.print("[red]Missing GROQ_API_KEY.[/red] Set it in your environment and retry.")
        raise typer.Exit(code=1)

    return Groq(api_key=api_key)


def generate_command(prompt: str, os_name: str, shell_name: str) -> str:
    client = ensure_groq()
    file_context = get_directory_context()
    system_prompt = build_system_prompt(os_name, shell_name, file_context)

    # --- MEMORY LOGIC START ---
    # 1. Load past conversation
    history = load_history()

    # 2. Build the full message chain: System -> History -> Current User Prompt
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt.strip()})
    # --- MEMORY LOGIC END ---

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0,
        )
    except Exception as exc:
        console.print(f"[red]Groq API error:[/red] {exc}")
        raise typer.Exit(code=1)

    content = response.choices[0].message.content or ""
    command = strip_command(content)
    if not command:
        console.print("[red]No command returned by model.[/red]")
        raise typer.Exit(code=1)

    # --- SAVE TO MEMORY ---
    # Append the new interaction and save it
    history.append({"role": "user", "content": prompt.strip()})
    history.append({"role": "assistant", "content": command})
    save_history(history)

    return command


def run_command(command: str, shell_path: str) -> int:
    try:
        completed = subprocess.run(command, shell=True, executable=shell_path)
    except FileNotFoundError as exc:
        console.print(f"[red]Shell not found:[/red] {exc}")
        raise typer.Exit(code=1)

    return completed.returncode


def show_command(command: str, shell_name: str) -> None:
    console.print("[bold]Proposed command:[/bold]")
    syntax = Syntax(command, syntax_lexer(shell_name), theme="monokai", line_numbers=False)
    console.print(syntax)


def handle_prompt(
    prompt: str,
    os_name: str,
    shell_name: str,
    shell_path: str,
    exit_on_abort: bool,
) -> None:
    command = generate_command(prompt, os_name, shell_name)
    show_command(command, shell_name)

    if not Confirm.ask("Run this command?", default=False):
        console.print("[yellow]Aborted.[/yellow]")
        if exit_on_abort:
            raise typer.Exit(code=0)
        return

    exit_code = run_command(command, shell_path)
    if exit_code != 0:
        console.print(f"[red]Command exited with code {exit_code}.[/red]")
        if exit_on_abort:
            raise typer.Exit(code=exit_code)


def interactive_loop(os_name: str, shell_name: str, shell_path: str) -> None:
    console.print("[bold]Tell[/bold] interactive mode. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            prompt = Prompt.ask("Describe a task")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not prompt.strip():
            continue
        if prompt.strip().lower() in {"exit", "quit"}:
            break

        # Add support for 'clear' inside interactive mode
        if prompt.strip().lower() == "clear":
            clear_history()
            console.print("[green]History cleared.[/green]")
            continue

        handle_prompt(prompt, os_name, shell_name, shell_path, exit_on_abort=False)


@app.command()
def main(
    prompt: Optional[str] = typer.Argument(None, help="Natural language task description."),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Start interactive mode."
    ),
    clear: bool = typer.Option(
        False, "--clear", help="Clear conversation history."
    ),
) -> None:
    """Generate a shell command using Groq and optionally execute it."""

    # --- HANDLE CLEAR FLAG ---
    if clear:
        clear_history()
        console.print("[green]Conversation history cleared.[/green]")
        raise typer.Exit()

    os_name = detect_os()
    shell_name, shell_path = detect_shell()

    if interactive or prompt is None:
        interactive_loop(os_name, shell_name, shell_path)
        return

    handle_prompt(prompt, os_name, shell_name, shell_path, exit_on_abort=True)


if __name__ == "__main__":
    app()
