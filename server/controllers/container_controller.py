"""HTTP controller for container resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, ServiceValidationError


class ContainerController:
    """Translate HTTP payloads into ContainerService operations."""

    def __init__(self, service):
        self.service = service

    def list_containers(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        return [self._to_payload(item) for item in self.service.list_containers()]

    def get_container(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self._to_payload(self.service.get_container(params["code"]))

    def create_container(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_container(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_container(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self._to_payload(self.service.update_container(params["code"], payload))

    def delete_container(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_container(params["code"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "code": dto.code,
            "type_name": dto.type_name,
            "last_update": dto.last_update.isoformat() if dto.last_update else None,
        }
