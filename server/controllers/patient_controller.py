"""HTTP controller for patient resources."""

from __future__ import annotations

from typing import Any

from shared.errors import BadRequestError, ConflictError, NotFoundError
from shared.errors import ServiceValidationError


class PatientController:
    """Translate HTTP payloads into PatientService operations."""

    def __init__(self, service):
        self.service = service

    def list_patients(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query = request.get("query", {})
        active = query.get("active")
        if active is not None and active.lower() not in {"true", "false"}:
            raise BadRequestError("Invalid active filter")
        active_only = None if active is None else active.lower() == "true"
        return [self._to_payload(item) for item in self.service.list_patients(active_only)]

    def list_samples(self, request: dict[str, Any], params: dict[str, str]) -> list[dict[str, Any]]:
        code = params["code"]
        return [self._sample_to_payload(item) for item in self.service.list_samples_for_patient(code)]

    def get_patient(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        code = params["code"]
        return self._to_payload(self.service.get_patient(code))

    def create_patient(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        try:
            created = self.service.create_patient(payload)
        except ConflictError:
            raise
        except ServiceValidationError as exc:
            raise ServiceValidationError(str(exc)) from exc
        return self._to_payload(created)

    def update_patient(self, request: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
        payload = request.get("body") or {}
        if not isinstance(payload, dict):
            raise BadRequestError("Request body must be a JSON object")
        code = params["code"]
        return self._to_payload(self.service.update_patient(code, payload))

    def delete_patient(self, request: dict[str, Any], params: dict[str, str]) -> None:
        self.service.delete_patient(params["code"])

    def _to_payload(self, dto) -> dict[str, Any]:
        return {
            "id": dto.id,
            "code": dto.code,
            "name": dto.name,
            "lastname": dto.lastname,
            "birth_date": dto.birth_date.isoformat() if dto.birth_date else None,
            "active": dto.active,
            "test": dto.test,
            "registration_date": dto.registration_date.isoformat() if dto.registration_date else None,
        }

    def _sample_to_payload(self, dto) -> dict[str, Any]:
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
