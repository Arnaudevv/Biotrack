"""Business logic for protocol resources."""

from __future__ import annotations

from datetime import date
from typing import Any

from server.persistence.repositories.protocol_repository import ProtocolRepository
from server.persistence.repositories.staff_repository import StaffRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import ProtocolDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class ProtocolService:
    """Manage protocol records and review assignments."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.protocol_repository = ProtocolRepository(uow.session)
        self.staff_repository = StaffRepository(uow.session)

    def list_protocols(self, keyword: str | None = None) -> list[ProtocolDTO]:
        if keyword:
            records = self.protocol_repository.search_by_name(keyword)
        else:
            records = self.protocol_repository.get_all()
        return [self._to_dto(record) for record in records]

    def get_protocol(self, code: str) -> ProtocolDTO:
        protocol = self.protocol_repository.get_by_code(code)
        if protocol is None:
            raise NotFoundError(f"Protocol '{code}' not found")
        return self._to_dto(protocol)

    def list_samples(self, code: str) -> list[dict[str, Any]]:
        protocol = self.protocol_repository.get_by_code(code)
        if protocol is None:
            raise NotFoundError(f"Protocol '{code}' not found")
        return [{
            "id": sample.id,
            "code": sample.code,
            "volume": str(sample.volume),
            "extraction_date": sample.extraction_date.isoformat() if sample.extraction_date else None,
            "status": sample.status,
            "patient_code": sample.patient.code if getattr(sample, "patient", None) else None,
            "sample_type": sample.sample_type.type_name if getattr(sample, "sample_type", None) else None,
            "container_code": sample.container.code if getattr(sample, "container", None) else None,
        } for sample in protocol.samples]

    def create_protocol(self, payload: dict[str, Any]) -> ProtocolDTO:
        dto = self._validate_create(payload)
        if self.protocol_repository.get_by_code(dto.code) is not None:
            raise ConflictError(f"Protocol '{dto.code}' already exists")
        if dto.reviewed_by:
            reviewer = self.staff_repository.get_by_code(dto.reviewed_by)
            if reviewer is None:
                raise NotFoundError(f"Staff '{dto.reviewed_by}' not found")
        protocol = self._dto_to_model(dto)
        self.uow.session.add(protocol)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(protocol)

    def update_protocol(self, code: str, payload: dict[str, Any]) -> ProtocolDTO:
        protocol = self.protocol_repository.get_by_code(code)
        if protocol is None:
            raise NotFoundError(f"Protocol '{code}' not found")
        if "name" in payload:
            protocol.name = payload["name"]
        if "description" in payload:
            protocol.description = payload["description"]
        if "reviewed_by" in payload:
            reviewer_code = payload["reviewed_by"]
            if reviewer_code in (None, ""):
                protocol.reviewed_by_id = None
            else:
                reviewer = self.staff_repository.get_by_code(reviewer_code)
                if reviewer is None:
                    raise NotFoundError(f"Staff '{reviewer_code}' not found")
                protocol.reviewed_by_id = reviewer.id
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(protocol)

    def delete_protocol(self, code: str) -> None:
        protocol = self.protocol_repository.get_by_code(code)
        if protocol is None:
            raise NotFoundError(f"Protocol '{code}' not found")
        self.uow.session.delete(protocol)

    def _validate_create(self, payload: dict[str, Any]) -> ProtocolDTO:
        required = ["code", "name"]
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                raise ServiceValidationError(f"Missing required field: {field}")
        code = payload["code"]
        name = payload["name"]
        if not isinstance(code, str) or not isinstance(name, str):
            raise ServiceValidationError("Code and name must be strings")
        description = payload.get("description")
        reviewed_by = payload.get("reviewed_by")
        if reviewed_by is not None and not isinstance(reviewed_by, str):
            raise ServiceValidationError("Reviewed by must be a staff code string")
        return ProtocolDTO(
            code=code,
            name=name,
            description=description,
            reviewed_by=reviewed_by,
        )

    def _dto_to_model(self, dto: ProtocolDTO):
        from server.persistence.models.protocol import Protocol as ProtocolModel
        protocol = ProtocolModel(
            code=dto.code,
            name=dto.name,
            description=dto.description,
        )
        if dto.reviewed_by:
            reviewer = self.staff_repository.get_by_code(dto.reviewed_by)
            if reviewer is not None:
                protocol.reviewed_by_id = reviewer.id
        return protocol

    def _to_dto(self, protocol) -> ProtocolDTO:
        return ProtocolDTO(
            id=protocol.id,
            code=protocol.code,
            name=protocol.name,
            description=protocol.description,
            reviewed_by=protocol.staff.code if getattr(protocol, "staff", None) else None,
            last_update=protocol.last_update,
        )
