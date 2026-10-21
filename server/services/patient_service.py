"""Business logic for patient resources."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from server.persistence.repositories.patient_repository import PatientRepository
from server.persistence.repositories.sample_repository import SampleRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import PatientDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class PatientService:
    """Manage patient records and their validation rules."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.patient_repository = PatientRepository(uow.session)
        self.sample_repository = SampleRepository(uow.session)

    def list_patients(self, active_only: bool | None = None) -> list[PatientDTO]:
        if active_only is None:
            records = self.patient_repository.get_all()
        else:
            records = self.patient_repository.get_active() if active_only else [
                p for p in self.patient_repository.get_all() if not p.active
            ]
        return [self._to_dto(record) for record in records]

    def get_patient(self, code: str) -> PatientDTO:
        patient = self.patient_repository.get_by_code(code)
        if patient is None:
            raise NotFoundError(f"Patient '{code}' not found")
        return self._to_dto(patient)

    def create_patient(self, payload: dict[str, Any]) -> PatientDTO:
        dto = self._validate_create(payload)
        if self.patient_repository.get_by_code(dto.code) is not None:
            raise ConflictError(f"Patient '{dto.code}' already exists")
        patient = self._dto_to_model(dto)
        self.uow.session.add(patient)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(patient)

    def update_patient(self, code: str, payload: dict[str, Any]) -> PatientDTO:
        patient = self.patient_repository.get_by_code(code)
        if patient is None:
            raise NotFoundError(f"Patient '{code}' not found")
        for field in ("name", "lastname", "birth_date", "test", "active"):
            if field in payload:
                value = payload[field]
                if field == "birth_date":
                    setattr(patient, field, self._parse_date(value, field))
                elif field == "active":
                    setattr(patient, field, bool(value))
                else:
                    setattr(patient, field, value)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(patient)

    def delete_patient(self, code: str) -> None:
        patient = self.patient_repository.get_by_code(code)
        if patient is None:
            raise NotFoundError(f"Patient '{code}' not found")
        if self.sample_repository.get_by_patient_code(code):
            raise ConflictError(f"Patient '{code}' still has samples")
        self.uow.session.delete(patient)

    def _to_dto(self, patient) -> PatientDTO:
        return PatientDTO(
            id=patient.id,
            code=patient.code,
            name=patient.name,
            lastname=patient.lastname,
            birth_date=patient.birth_date,
            active=bool(patient.active),
            test=patient.test,
            registration_date=patient.registration_date,
        )

    def _dto_to_model(self, dto: PatientDTO):
        from server.persistence.models.patient import Patient as PatientModel
        return PatientModel(
            code=dto.code,
            name=dto.name,
            lastname=dto.lastname,
            birth_date=dto.birth_date,
            active=dto.active,
            test=dto.test,
        )

    def _validate_create(self, payload: dict[str, Any]) -> PatientDTO:
        errors = []
        required = ["code", "name", "lastname", "birth_date"]
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                errors.append(f"Missing required field: {field}")
        if errors:
            raise ServiceValidationError("; ".join(errors))
        if not isinstance(payload["code"], str):
            raise ServiceValidationError("Code must be a string")
        if not isinstance(payload["name"], str) or not isinstance(payload["lastname"], str):
            raise ServiceValidationError("Name and lastname must be strings")
        birth_date = self._parse_date(payload["birth_date"], "birth_date")
        test = payload.get("test", "Routine checkup")
        if not isinstance(test, str):
            raise ServiceValidationError("Test must be a string")
        active = payload.get("active", True)
        if not isinstance(active, bool):
            raise ServiceValidationError("Active must be a boolean")
        return PatientDTO(
            code=payload["code"],
            name=payload["name"],
            lastname=payload["lastname"],
            birth_date=birth_date,
            test=test,
            active=active,
        )

    def _parse_date(self, value: Any, field_name: str) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ServiceValidationError(f"Invalid {field_name}: {value}") from exc
        raise ServiceValidationError(f"Invalid {field_name}: {value}")


from datetime import datetime
