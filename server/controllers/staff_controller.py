"""HTTP controller for staff resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, ServiceValidationError


class StaffController:
    """Translate HTTP payloads into StaffService operations."""

    def __init__(self, service):
        self.service = service

    def list_staff(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        return [self._to_payload(item) for item in self.service.list_staff()]

    def list_assignments(self, request: dict[str, Any], params: dict[str, str]) -> list[dict[str, Any]]:
        return self.service.list_assignments(params["code"])

    def get_staff(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self._to_payload(self.service.get_staff(params["code"]))

    def create_staff(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_staff(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_staff(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self._to_payload(self.service.update_staff(params["code"], payload))

    def delete_staff(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_staff(params["code"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "code": dto.code,
            "name": dto.name,
            "lastname": dto.lastname,
            "role": dto.role,
            "active": dto.active,
        }
