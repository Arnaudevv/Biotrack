"""Application-level router factory for the TCP server."""

from __future__ import annotations

from typing import Any, Callable

from shared.errors import BadRequestError, ConflictError, NotFoundError
from shared.errors import ServiceValidationError


def _match_path(pattern: str, path: str) -> dict[str, str] | None:
    """Match a route pattern to a request path and return path params."""
    pattern_parts = pattern.strip("/").split("/") if pattern != "/" else []
    path_parts = path.strip("/").split("/") if path != "/" else []
    if len(pattern_parts) != len(path_parts):
        return None
    params: dict[str, str] = {}
    for pattern_part, path_part in zip(pattern_parts, path_parts):
        if pattern_part.startswith("{") and pattern_part.endswith("}"):
            params[pattern_part[1:-1]] = path_part
        elif pattern_part != path_part:
            return None
    return params


def build_router() -> Callable[[dict[str, Any]], dict[str, Any] | list | None]:
    """Build the application router with all documented endpoints."""
    routes: list[tuple[str, str, Callable[..., Any]]] = []

    def register(method: str, path: str, handler: Callable[..., Any]) -> None:
        routes.append((method.upper(), path, handler))

    def ping_handler(request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return {"message": "pong"}

    def not_found_handler(request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        raise NotFoundError("Resource not found")

    register("GET", "/ping", ping_handler)
    register("GET", "/patients", not_found_handler)
    register("POST", "/patients", not_found_handler)
    register("GET", "/patients/{code}", not_found_handler)
    register("PATCH", "/patients/{code}", not_found_handler)
    register("DELETE", "/patients/{code}", not_found_handler)
    register("GET", "/patients/{code}/samples", not_found_handler)
    register("GET", "/samples", not_found_handler)
    register("POST", "/samples", not_found_handler)
    register("GET", "/samples/{code}", not_found_handler)
    register("GET", "/samples/{code}/full", not_found_handler)
    register("PATCH", "/samples/{code}", not_found_handler)
    register("DELETE", "/samples/{code}", not_found_handler)
    register("GET", "/samples/{code}/quality-control", not_found_handler)
    register("PUT", "/samples/{code}/quality-control", not_found_handler)
    register("POST", "/samples/{code}/protocols", not_found_handler)
    register("GET", "/staff", not_found_handler)
    register("POST", "/staff", not_found_handler)
    register("GET", "/staff/{code}", not_found_handler)
    register("PATCH", "/staff/{code}", not_found_handler)
    register("DELETE", "/staff/{code}", not_found_handler)
    register("GET", "/staff/{code}/assignments", not_found_handler)
    register("GET", "/projects", not_found_handler)
    register("POST", "/projects", not_found_handler)
    register("GET", "/projects/{id}", not_found_handler)
    register("PATCH", "/projects/{id}", not_found_handler)
    register("DELETE", "/projects/{id}", not_found_handler)
    register("POST", "/projects/{id}/samples", not_found_handler)
    register("POST", "/projects/{id}/team", not_found_handler)
    register("GET", "/protocols", not_found_handler)
    register("POST", "/protocols", not_found_handler)
    register("GET", "/protocols/{code}", not_found_handler)
    register("PATCH", "/protocols/{code}", not_found_handler)
    register("DELETE", "/protocols/{code}", not_found_handler)
    register("GET", "/protocols/{code}/samples", not_found_handler)
    register("GET", "/containers", not_found_handler)
    register("POST", "/containers", not_found_handler)
    register("GET", "/sample-types", not_found_handler)
    register("POST", "/sample-types", not_found_handler)

    def router(request: dict[str, Any]) -> dict[str, Any] | list | None:
        method = request.get("method", "GET").upper()
        path = request.get("path", "/")
        params: dict[str, str] | None = None
        matched: tuple[str, str, Callable[..., Any]] | None = None

        for route_method, route_path, handler in routes:
            if route_method != method:
                continue
            params = _match_path(route_path, path)
            if params is not None:
                matched = (route_method, route_path, handler)
                break

        if matched is None:
            for route_method, route_path, _ in routes:
                if route_path == path and route_method != method:
                    raise BadRequestError(f"Method {method} not allowed for {path}")
            for route_method, route_path, _ in routes:
                if _match_path(route_path, path) is not None:
                    raise BadRequestError(f"Method {method} not allowed for {path}")
            raise NotFoundError(f"Route not found: {path}")

        handler = matched[2]
        try:
            return handler(request, params or {})
        except (NotFoundError, ConflictError, ServiceValidationError) as exc:
            raise exc

    return router
