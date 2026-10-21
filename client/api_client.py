"""High-level API client for the BioTrack TCP server."""

from __future__ import annotations

from client.connection import send_request


def ping() -> dict:
    """Check that the server is reachable."""
    return send_request("GET", "/ping")


def list_patients(active_only: bool = False) -> list[dict] | dict:
    """List all patients or only those matching the active filter."""
    path = "/patients?active=true" if active_only else "/patients"
    return send_request("GET", path)
