"""HTTP controller for sample resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, ServiceValidationError


class SampleController:
    """Translate HTTP payloads into SampleService operations."""

    def __init__(self, service):
        self.service = service

    def list_samples(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query = request.get("query", {})
        status = query.get("status")
        return [self._to_payload(item) for item in self.service.list_samples(status)]

    def get_sample(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self._to_payload(self.service.get_sample(params["code"]))

    def get_full_sample(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self.service.get_full_sample(params["code"])

    def get_quality_control(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        return self.service.get_quality_control(params["code"])

    def set_quality_control(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self.service.set_quality_control(params["code"], payload)

    def apply_protocol(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        protocol_code = payload.get("protocol_code")
        if not protocol_code:
            raise BadRequestError("Missing required field: protocol_code")
        return self.service.apply_protocol(params["code"], protocol_code)

    def create_sample(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_sample(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_sample(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        return self._to_payload(self.service.update_sample(params["code"], payload))

    def delete_sample(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_sample(params["code"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "code": dto.code,
            "volume": str(dto.volume) if dto.volume is not None else None,
            "extraction_date": dto.extraction_date.isoformat() if dto.extraction_date else None,
            "status": dto.status,
            "patient_code": dto.patient_code,
            "sample_type": dto.sample_type,
            "container_code": dto.container_code,
        }
