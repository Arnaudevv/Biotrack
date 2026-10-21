"""Minimal client entry point for the BioTrack TCP stack."""

from __future__ import annotations

import sys

try:
    from rich.console import Console
except ImportError:  # pragma: no cover - optional CLI dependency
    Console = None

from client.api_client import ping


def show_banner() -> None:
    """Display a small banner in the terminal."""
    if Console is None:
        print("BioTrack CLI")
        return
    console = Console()
    console.print("[bold cyan]BioTrack[/bold cyan] [white]TCP client[/white]")


def main() -> None:
    """Start the client terminal application."""
    show_banner()
    try:
        response = ping()
        if Console is None:
            print(response)
        else:
            Console().print(response)
    except Exception as exc:  # pragma: no cover - network errors are handled at runtime
        message = f"Cannot reach the server: {exc}"
        if Console is None:
            print(message)
        else:
            Console().print(f"[bold red]{message}[/bold red]")


if __name__ == "__main__":
    main()
    sys.exit(0)
