"""Shared testing helpers for protocol and socket-oriented tests."""

from __future__ import annotations

import socket
from typing import Iterable


class FakeSocket:
    """Simple socket stub that yields chunks from a predefined byte stream."""

    def __init__(self, chunks: Iterable[bytes], *, close_after: bool = False):
        self._chunks = list(chunks)
        self._index = 0
        self.sent = bytearray()
        self.closed = False
        self.close_after = close_after

    def recv(self, size: int = 4096) -> bytes:
        if self.closed and self._index >= len(self._chunks):
            return b""
        if self._index >= len(self._chunks):
            return b""
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk[:size]

    def sendall(self, data: bytes) -> None:
        self.sent.extend(data)

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def close(self) -> None:
        self.closed = True


def make_request(method: str, path: str, body: dict | None = None) -> bytes:
    """Create a minimal protocol request by hand."""
    import json

    payload = b""
    if body is not None:
        payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = [
        f"{method} {path} HTTP/1.1",
        "Host: 127.0.0.1:8000",
        "Connection: close",
    ]
    if body is not None:
        headers.append("Content-Type: application/json")
    headers.append(f"Content-Length: {len(payload)}")
    return ("\r\n".join(headers) + "\r\n\r\n").encode("iso-8859-1") + payload


def make_response(status: int, body: dict | list | None = None) -> bytes:
    """Create a minimal protocol response by hand."""
    import json

    payload = b""
    if body is not None:
        payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
    reason = {
        200: "OK",
        201: "Created",
        204: "No Content",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }.get(status, "OK")
    headers = [
        f"HTTP/1.1 {status} {reason}",
        "Content-Type: application/json; charset=utf-8",
        "Connection: close",
        f"Content-Length: {len(payload)}",
    ]
    return ("\r\n".join(headers) + "\r\n\r\n").encode("iso-8859-1") + payload
