"""Blocking TCP server implementation for the BioTrack protocol."""

from __future__ import annotations

import logging
import socket
from typing import Any, Callable

from server.settings import BUFFER_SIZE, HOST, LISTEN_BACKLOG, PORT
from server.settings import READ_TIMEOUT_SECONDS
from shared.errors import BadRequestError, ConflictError, MethodNotAllowedError
from shared.errors import NotFoundError, ServiceValidationError
from shared.protocol import build_response, parse_request, read_http_message

LOGGER = logging.getLogger("biotrack.server")


def _error_response(error: Exception) -> bytes:
    mapping = {
        BadRequestError: (400, "Bad Request"),
        MethodNotAllowedError: (405, "Method Not Allowed"),
        NotFoundError: (404, "Not Found"),
        ConflictError: (409, "Conflict"),
        ServiceValidationError: (422, "Unprocessable Entity"),
    }
    status, reason = mapping.get(type(error), (500, "Internal Server Error"))
    detail = str(error) if str(error) else reason
    body = {"detail": detail}
    return build_response(status, body, reason)


def handle_connection(conn: socket.socket, handler: Callable[[dict[str, Any]], Any]) -> None:
    """Handle one client request and send one HTTP-like response back."""
    conn.settimeout(READ_TIMEOUT_SECONDS)
    try:
        raw = read_http_message(conn)
        if not raw:
            conn.sendall(build_response(400, {"detail": "Empty request"}, "Bad Request"))
            return
        request = parse_request(raw)
    except TimeoutError:
        conn.sendall(build_response(408, {"detail": "Request timeout"}, "Request Timeout"))
        return
    except ValueError as exc:
        conn.sendall(build_response(400, {"detail": str(exc)}, "Bad Request"))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        LOGGER.exception("Failed to parse request")
        conn.sendall(build_response(500, {"detail": str(exc)}, "Internal Server Error"))
        return

    try:
        result = handler(request)
    except (BadRequestError, ConflictError, MethodNotAllowedError,
            NotFoundError, ServiceValidationError, ValueError) as exc:
        conn.sendall(_error_response(exc))
        return
    except Exception as exc:  # pragma: no cover - defensive fallback
        LOGGER.exception("Unhandled server error")
        conn.sendall(build_response(500, {"detail": str(exc)}, "Internal Server Error"))
        return

    if isinstance(result, (bytes, bytearray)):
        conn.sendall(result)
        return
    status = 200
    if result is None:
        payload = None
        status = 204
    else:
        payload = result
    conn.sendall(build_response(status, payload))


def serve(handler: Callable[[dict[str, Any]], Any], host: str = HOST, port: int = PORT):
    """Serve one client at a time on the configured TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(LISTEN_BACKLOG)
        server_socket.settimeout(1)
        LOGGER.info("Listening on %s:%s", host, port)

        while True:
            try:
                conn, _ = server_socket.accept()
            except socket.timeout:
                continue
            with conn:
                handle_connection(conn, handler)
