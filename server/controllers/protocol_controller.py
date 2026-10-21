"""HTTP controller for protocol resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, ServiceValidationError


class ProtocolController:
    """Translate HTTP payloads into ProtocolService operations."""

    def __init__(self, service):
        self.service = service

    def list_protocols(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query = request.get("query", {})
        keyword = query.get("keyword")
        return [self._to_payload(item) for item in self.service.list_protocols(keyword)]

    def list_samples(self, request: dict[str, Any], params: dict[str, str]) -> list[dict[str, Any]]:
        return self.service.list_samples(params["code"])

    def get_protocol(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self._to_payload(self.service.get_protocol(params["code"]))

    def create_protocol(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_protocol(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_protocol(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self._to_payload(self.service.update_protocol(params["code"], payload))

    def delete_protocol(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_protocol(params["code"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "code": dto.code,
            "name": dto.name,
            "description": dto.description,
            "reviewed_by": dto.reviewed_by,
            "last_update": dto.last_update.isoformat() if dto.last_update else None,
        }
