"""Business logic for sample resources."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from server.persistence.repositories.container_repository import ContainerRepository
from server.persistence.repositories.patient_repository import PatientRepository
from server.persistence.repositories.protocol_repository import ProtocolRepository
from server.persistence.repositories.quality_control_repository import QualityControlRepository
from server.persistence.repositories.sample_repository import SampleRepository
from server.persistence.repositories.sample_type_repository import SampleTypeRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import SampleDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class SampleService:
    """Manage sample records and validation rules."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.sample_repository = SampleRepository(uow.session)
        self.patient_repository = PatientRepository(uow.session)
        self.sample_type_repository = SampleTypeRepository(uow.session)
        self.container_repository = ContainerRepository(uow.session)
        self.protocol_repository = ProtocolRepository(uow.session)
        self.quality_control_repository = QualityControlRepository(uow.session)

    def list_samples(self, status: str | None = None) -> list[SampleDTO]:
        if status:
            records = self.sample_repository.get_by_status(status)
        else:
            records = self.sample_repository.get_all()
        return [self._to_dto(record) for record in records]

    def list_samples_for_patient(self, patient_code: str) -> list[SampleDTO]:
        patient = self.patient_repository.get_by_code(patient_code)
        if patient is None:
            raise NotFoundError(f"Patient '{patient_code}' not found")
        return [self._to_dto(record) for record in self.sample_repository.get_by_patient_code(patient_code)]

    def get_sample(self, code: str) -> SampleDTO:
        sample = self.sample_repository.get_by_code(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        return self._to_dto(sample)

    def get_full_sample(self, code: str) -> dict[str, Any]:
        sample = self.sample_repository.get_full(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        patient = sample.patient
        quality_control = sample.quality_control
        return {
            "id": sample.id,
            "code": sample.code,
            "volume": str(sample.volume),
            "extraction_date": sample.extraction_date.isoformat() if sample.extraction_date else None,
            "status": sample.status,
            "patient": {"code": patient.code, "name": patient.name, "lastname": patient.lastname},
            "sample_type": sample.sample_type.type_name if getattr(sample, "sample_type", None) else None,
            "container_code": sample.container.code if getattr(sample, "container", None) else None,
            "quality_control": None if quality_control is None else {
                "sample_code": sample.code,
                "purity": str(quality_control.purity) if quality_control.purity is not None else None,
                "concentration": str(quality_control.concentration) if quality_control.concentration is not None else None,
                "result": quality_control.result,
            },
            "protocols": [{"code": protocol.code, "name": protocol.name} for protocol in sample.protocols],
            "temperature_logs": [{
                "id": log.id,
                "reading_date": log.reading_date.isoformat() if log.reading_date else None,
                "temperature": str(log.temperature),
            } for log in sample.log_temperatures],
            "projects": [{
                "id": project.id,
                "project_name": project.project_name,
                "assignment_date": None,
            } for project in sample.research_projects],
        }

    def get_quality_control(self, code: str) -> dict[str, Any]:
        sample = self.sample_repository.get_by_code(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        qc = sample.quality_control
        if qc is None:
            raise NotFoundError(f"Quality control for sample '{code}' not found")
        return {
            "sample_code": sample.code,
            "purity": str(qc.purity) if qc.purity is not None else None,
            "concentration": str(qc.concentration) if qc.concentration is not None else None,
            "result": qc.result,
        }

    def set_quality_control(self, code: str, payload: dict[str, Any]) -> dict[str, Any]:
        sample = self.sample_repository.get_by_code(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        if not isinstance(payload, dict):
            raise ServiceValidationError("Quality control payload must be an object")

        result = payload.get("result")
        if result is None or str(result).strip() == "":
            raise ServiceValidationError("Missing required field: result")
        result = str(result).strip()
        valid = {"approved", "rejected", "pending_review"}
        if result not in valid:
            raise ServiceValidationError(f"Result must be one of: {sorted(valid)}")

        purity_value = payload.get("purity")
        if purity_value is not None:
            purity = self._parse_decimal(purity_value, "purity")
            if purity < 0 or purity > 100:
                raise ServiceValidationError("Purity must be between 0 and 100")
        else:
            purity = None

        concentration_value = payload.get("concentration")
        if concentration_value is not None:
            concentration = self._parse_decimal(concentration_value, "concentration")
            if concentration < 0:
                raise ServiceValidationError("Concentration must be greater than or equal to 0")
        else:
            concentration = None

        if sample.quality_control is None:
            from server.persistence.models.quality_control import QualityControl as QualityControlModel
            qc = QualityControlModel(
                purity=purity,
                concentration=concentration,
                result=result,
                sample=sample,
            )
            self.uow.session.add(qc)
        else:
            qc = sample.quality_control
            qc.purity = purity
            qc.concentration = concentration
            qc.result = result

        self.uow.session.flush()
        return self.get_quality_control(code)

    def apply_protocol(self, code: str, protocol_code: str) -> dict[str, Any]:
        sample = self.sample_repository.get_by_code(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        protocol = self.protocol_repository.get_by_code(protocol_code)
        if protocol is None:
            raise NotFoundError(f"Protocol '{protocol_code}' not found")
        if any(existing.code == protocol_code for existing in sample.protocols):
            raise ConflictError(f"Protocol '{protocol_code}' is already applied to sample '{code}'")
        sample.protocols.append(protocol)
        self.uow.session.flush()
        return {"sample_code": sample.code, "protocol_code": protocol.code}

    def create_sample(self, payload: dict[str, Any]) -> SampleDTO:
        dto = self._validate_create(payload)
        if self.sample_repository.get_by_code(dto.code) is not None:
            raise ConflictError(f"Sample '{dto.code}' already exists")
        patient = self.patient_repository.get_by_code(dto.patient_code)
        if patient is None:
            raise NotFoundError(f"Patient '{dto.patient_code}' not found")
        sample_type = self.sample_type_repository.get_by_name(dto.sample_type)
        if sample_type is None:
            raise NotFoundError(f"Sample type '{dto.sample_type}' not found")
        container = self.container_repository.get_by_code(dto.container_code)
        if container is None:
            raise NotFoundError(f"Container '{dto.container_code}' not found")
        sample = self._dto_to_model(dto, patient.id, sample_type.id, container.id)
        self.uow.session.add(sample)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(sample)

    def update_sample(self, code: str, payload: dict[str, Any]) -> SampleDTO:
        sample = self.sample_repository.get_by_code(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        for field in ("volume", "extraction_date", "status"):
            if field in payload:
                value = payload[field]
                if field == "volume":
                    sample.volume = self._parse_decimal(value, "volume")
                elif field == "extraction_date":
                    sample.extraction_date = self._parse_date(value, "extraction_date")
                else:
                    sample.status = self._validate_status(value)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(sample)

    def delete_sample(self, code: str) -> None:
        sample = self.sample_repository.get_by_code(code)
        if sample is None:
            raise NotFoundError(f"Sample '{code}' not found")
        self.uow.session.delete(sample)

    def _validate_create(self, payload: dict[str, Any]) -> SampleDTO:
        required = ["code", "volume", "extraction_date", "patient_code", "sample_type", "container_code"]
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                raise ServiceValidationError(f"Missing required field: {field}")
        if not isinstance(payload["code"], str):
            raise ServiceValidationError("Code must be a string")
        volume = self._parse_decimal(payload["volume"], "volume")
        if volume <= 0:
            raise ServiceValidationError("Volume must be greater than zero")
        status = self._validate_status(payload.get("status", "pending"))
        return SampleDTO(
            code=payload["code"],
            volume=volume,
            extraction_date=self._parse_date(payload["extraction_date"], "extraction_date"),
            status=status,
            patient_code=payload["patient_code"],
            sample_type=payload["sample_type"],
            container_code=payload["container_code"],
        )

    def _validate_status(self, value: Any) -> str:
        valid = {"pending", "in_process", "analyzed", "rejected", "archived"}
        if value is None:
            raise ServiceValidationError("Status is required")
        status = str(value).strip()
        if status not in valid:
            raise ServiceValidationError(f"Status must be one of: {sorted(valid)}")
        return status

    def _parse_decimal(self, value: Any, field_name: str) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float, str)):
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                raise ServiceValidationError(f"Invalid {field_name}: {value}") from exc
        raise ServiceValidationError(f"Invalid {field_name}: {value}")

    def _parse_date(self, value: Any, field_name: str) -> date:
        if isinstance(value, date) and not isinstance(value, str):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ServiceValidationError(f"Invalid {field_name}: {value}") from exc
        raise ServiceValidationError(f"Invalid {field_name}: {value}")

    def _dto_to_model(self, dto: SampleDTO, patient_id: int, sample_type_id: int, container_id: int):
        from server.persistence.models.sample import Sample as SampleModel
        return SampleModel(
            code=dto.code,
            volume=dto.volume,
            extraction_date=dto.extraction_date,
            status=dto.status,
            id_patient=patient_id,
            id_sample_type=sample_type_id,
            id_container=container_id,
        )

    def _to_dto(self, sample) -> SampleDTO:
        return SampleDTO(
            id=sample.id,
            code=sample.code,
            volume=Decimal(str(sample.volume)),
            extraction_date=sample.extraction_date,
            status=sample.status,
            patient_code=sample.patient.code if getattr(sample, "patient", None) else None,
            sample_type=sample.sample_type.type_name if getattr(sample, "sample_type", None) else None,
            container_code=sample.container.code if getattr(sample, "container", None) else None,
        )
