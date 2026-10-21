"""Client connection layer for socket-based communication."""

from __future__ import annotations

import socket

from client.settings import BUFFER_SIZE, HOST, PORT, TIMEOUT_SECONDS
from shared.errors import ApiError
from shared.protocol import build_request, parse_response


def send_request(method: str, path: str, body: dict | None = None) -> dict:
    """Send one request to the server and return the parsed JSON payload."""
    request = build_request(method, path, body, host=f"{HOST}:{PORT}")
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT_SECONDS) as sock:
            sock.sendall(request)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                chunks.append(chunk)
    except OSError as exc:
        raise ApiError(0, f"Cannot reach the server: {exc}") from exc

    raw = b"".join(chunks)
    if not raw:
        raise ApiError(0, "Empty response from server")

    response = parse_response(raw)
    status = response["status"]
    payload = response["body"]
    if status >= 400:
        detail = payload.get("detail") if isinstance(payload, dict) else str(payload)
        raise ApiError(status, detail, payload)
    return payload if payload is not None else {}
