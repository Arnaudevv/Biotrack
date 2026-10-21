"""HTTP controller for sample type resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, ServiceValidationError


class SampleTypeController:
    """Translate HTTP payloads into SampleTypeService operations."""

    def __init__(self, service):
        self.service = service

    def list_sample_types(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        return [self._to_payload(item) for item in self.service.list_sample_types()]

    def get_sample_type(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self._to_payload(self.service.get_sample_type(params["type_name"]))

    def create_sample_type(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_sample_type(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_sample_type(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self._to_payload(self.service.update_sample_type(params["type_name"], payload))

    def delete_sample_type(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_sample_type(params["type_name"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "type_name": dto.type_name,
            "last_update": dto.last_update.isoformat() if dto.last_update else None,
        }
