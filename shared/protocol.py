import json
import socket
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from shared.dtos import dto_from_dict, dto_to_dict

CRLF = "\r\n"
DEFAULT_HOST = "127.0.0.1:8000"
MAX_START_LINE_AND_HEADERS = 8192
MAX_BODY_SIZE = 1_048_576
SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def percent_encode(value: str, safe: str = "") -> str:
    """Percent-encode a string without using urllib.parse."""
    if value is None:
        return ""
    encoded = []
    for char in value:
        if char.isalnum() or char in safe or char in "-_.~":
            encoded.append(char)
        elif char == " ":
            encoded.append("%20")
        else:
            encoded.append(f"%{ord(char):02X}")
    return "".join(encoded)


def percent_decode(value: str) -> str:
    """Percent-decode a string without using urllib.parse."""
    if value is None:
        return ""
    result = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "+":
            result.append(" ")
            index += 1
            continue
        if char == "%" and index + 2 < len(value):
            try:
                result.append(chr(int(value[index + 1:index + 3], 16)))
                index += 3
                continue
            except ValueError:
                pass
        result.append(char)
        index += 1
    return "".join(result)


def _coerce_json(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _coerce_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_coerce_json(item) for item in value]
    return value


def build_request(method: str, path: str, body: dict | None = None,
                  host: str = DEFAULT_HOST) -> bytes:
    """Build an HTTP-like request following docs/protocol.md."""
    if method.upper() not in SUPPORTED_METHODS:
        raise ValueError(f"Unsupported HTTP method: {method}")
    payload = b""
    if body is not None:
        serialized = json.dumps(_coerce_json(body), separators=(",", ":"), ensure_ascii=False)
        payload = serialized.encode("utf-8")
    lines = [
        f"{method.upper()} {path} HTTP/1.1",
        f"Host: {host}",
        "Connection: close",
    ]
    if body is not None:
        lines.append("Content-Type: application/json")
    lines.append(f"Content-Length: {len(payload)}")
    request_bytes = (CRLF.join(lines) + CRLF + CRLF).encode("iso-8859-1")
    return request_bytes + payload


def parse_query_string(query: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not query:
        return result
    pairs = query.split("&")
    for pair in pairs:
        if not pair:
            continue
        if "=" in pair:
            key, value = pair.split("=", 1)
        else:
            key, value = pair, ""
        result[percent_decode(key)] = percent_decode(value)
    return result


def _parse_headers(header_block: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in header_block.split(CRLF):
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Malformed header: {line}")
        name, value = line.split(":", 1)
        key = name.strip().lower()
        headers[key] = value.strip()
    return headers


def parse_request(raw: bytes) -> dict[str, Any]:
    """Parse an HTTP request and return a normalized dict."""
    if not raw:
        raise ValueError("Empty request")
    if b"\r\n\r\n" not in raw:
        raise ValueError("Request missing header terminator")
    head, body = raw.split(b"\r\n\r\n", 1)
    start_line, _, header_block = head.decode("iso-8859-1").partition(CRLF)
    if not start_line:
        raise ValueError("Missing request line")
    tokens = start_line.split(" ")
    if len(tokens) != 3:
        raise ValueError("Request line must have 3 tokens")
    method, target, version = tokens
    if version != "HTTP/1.1":
        raise ValueError("Unsupported HTTP version")
    if method.upper() not in SUPPORTED_METHODS:
        raise ValueError(f"Unsupported method: {method}")
    if not target.startswith("/"):
        raise ValueError("Target must start with /")
    headers = _parse_headers(header_block)
    if "transfer-encoding" in headers:
        raise ValueError("Transfer-Encoding is not supported")
    if "content-length" not in headers:
        content_length = 0
    else:
        try:
            content_length = int(headers["content-length"])
        except ValueError as exc:
            raise ValueError("Content-Length must be numeric") from exc
        if content_length < 0:
            raise ValueError("Content-Length cannot be negative")
        if content_length > MAX_BODY_SIZE:
            raise ValueError("Payload too large")
    if len(body) < content_length:
        raise ValueError("Request body is shorter than Content-Length")
    if len(body) > content_length:
        body = body[:content_length]
    payload = body.decode("utf-8") if content_length else ""
    parsed_body = json.loads(payload) if payload else None
    if parsed_body is not None and not isinstance(parsed_body, dict):
        raise ValueError("Request body must be a JSON object")
    if "content-type" in headers and headers["content-type"] != "application/json" and content_length:
        raise ValueError("Content-Type must be application/json")
    path, _, query = target.partition("?")
    return {
        "method": method.upper(),
        "path": percent_decode(path),
        "query": parse_query_string(query),
        "headers": headers,
        "body": parsed_body,
    }


def build_response(status: int, body: Any = None, reason: str | None = None,
                   headers: dict[str, str] | None = None) -> bytes:
    """Build an HTTP response message."""
    status_text = {
        200: "OK",
        201: "Created",
        204: "No Content",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Request Timeout",
        409: "Conflict",
        413: "Payload Too Large",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }.get(status, reason or "OK")
    response_headers = {"Content-Type": "application/json; charset=utf-8", "Connection": "close"}
    if headers:
        response_headers.update(headers)
    payload = b""
    if body is not None and status != 204:
        serialized = json.dumps(_coerce_json(body), ensure_ascii=False, separators=(",", ":"))
        payload = serialized.encode("utf-8")
    response_headers["Content-Length"] = str(len(payload))
    lines = [f"HTTP/1.1 {status} {status_text}"]
    for key, value in response_headers.items():
        lines.append(f"{key}: {value}")
    response = (CRLF.join(lines) + CRLF + CRLF).encode("iso-8859-1")
    return response + payload


def parse_response(raw: bytes) -> dict[str, Any]:
    """Parse an HTTP response message and return a normalized dictionary."""
    if not raw:
        raise ValueError("Empty response")
    if b"\r\n\r\n" not in raw:
        raise ValueError("Response missing header terminator")
    head, body = raw.split(b"\r\n\r\n", 1)
    status_line, _, header_block = head.decode("iso-8859-1").partition(CRLF)
    if not status_line:
        raise ValueError("Missing status line")
    parts = status_line.split(" ")
    if len(parts) < 3:
        raise ValueError("Malformed status line")
    try:
        status = int(parts[1])
    except ValueError as exc:
        raise ValueError("Status must be numeric") from exc
    headers = _parse_headers(header_block)
    content_length = int(headers.get("content-length", "0"))
    if len(body) < content_length:
        raise ValueError("Response body is shorter than Content-Length")
    body_bytes = body[:content_length]
    payload = None
    if content_length > 0:
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            payload = body_bytes.decode("utf-8", errors="replace")
    return {"status": status, "headers": headers, "body": payload}


def read_http_message(sock: socket.socket, max_headers: int = MAX_START_LINE_AND_HEADERS,
                     max_body: int = MAX_BODY_SIZE) -> bytes:
    """Read one HTTP message from a socket-like object."""
    buffer = bytearray()
    while b"\r\n\r\n" not in buffer:
        try:
            chunk = sock.recv(4096)
        except socket.timeout as exc:
            raise TimeoutError("Request timeout") from exc
        except OSError as exc:
            raise ValueError("Socket closed unexpectedly") from exc
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_headers:
            raise ValueError("Headers exceed limit")
    if not buffer:
        return b""

    header_bytes, _, remainder = buffer.partition(b"\r\n\r\n")
    if not remainder:
        header_text = header_bytes.decode("iso-8859-1", errors="replace")
        content_length = 0
        for line in header_text.split(CRLF):
            if line.lower().startswith("content-length:"):
                _, value = line.split(":", 1)
                content_length = int(value.strip())
                break
        if content_length <= 0:
            return bytes(header_bytes + b"\r\n\r\n")
        body = bytearray()
        while len(body) < content_length:
            try:
                chunk = sock.recv(min(4096, content_length - len(body)))
            except socket.timeout as exc:
                raise TimeoutError("Request timeout") from exc
            except OSError as exc:
                raise ValueError("Socket closed unexpectedly") from exc
            if not chunk:
                raise ValueError("Incomplete HTTP message")
            body.extend(chunk)
            if len(body) > max_body:
                raise ValueError("Payload too large")
        return bytes(header_bytes + b"\r\n\r\n" + body)

    message = bytearray(header_bytes + b"\r\n\r\n" + remainder)
    header_text = header_bytes.decode("iso-8859-1", errors="replace")
    content_length = 0
    for line in header_text.split(CRLF):
        if line.lower().startswith("content-length:"):
            _, value = line.split(":", 1)
            content_length = int(value.strip())
            break
    if content_length <= 0:
        return bytes(message)
    while len(remainder) < content_length:
        try:
            chunk = sock.recv(min(4096, content_length - len(remainder)))
        except socket.timeout as exc:
            raise TimeoutError("Request timeout") from exc
        except OSError as exc:
            raise ValueError("Socket closed unexpectedly") from exc
        if not chunk:
            raise ValueError("Incomplete HTTP message")
        remainder.extend(chunk)
        if len(remainder) > max_body:
            raise ValueError("Payload too large")
    return bytes(header_bytes + b"\r\n\r\n" + remainder[:content_length])


__all__ = [
    "DEFAULT_HOST", "MAX_BODY_SIZE", "CRLF",
    "build_request", "build_response", "parse_request", "parse_response",
    "percent_encode", "percent_decode", "read_http_message", "dto_to_dict",
    "dto_from_dict",
]
