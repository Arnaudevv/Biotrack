"""Business logic for sample type resources."""

from __future__ import annotations

from typing import Any

from server.persistence.repositories.sample_type_repository import SampleTypeRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import SampleTypeDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class SampleTypeService:
    """Manage sample-type records."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.sample_type_repository = SampleTypeRepository(uow.session)

    def list_sample_types(self) -> list[SampleTypeDTO]:
        return [self._to_dto(record) for record in self.sample_type_repository.get_all()]

    def get_sample_type(self, type_name: str) -> SampleTypeDTO:
        sample_type = self.sample_type_repository.get_by_name(type_name)
        if sample_type is None:
            raise NotFoundError(f"Sample type '{type_name}' not found")
        return self._to_dto(sample_type)

    def create_sample_type(self, payload: dict[str, Any]) -> SampleTypeDTO:
        dto = self._validate_create(payload)
        if self.sample_type_repository.get_by_name(dto.type_name) is not None:
            raise ConflictError(f"Sample type '{dto.type_name}' already exists")
        sample_type = self._dto_to_model(dto)
        self.uow.session.add(sample_type)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(sample_type)

    def update_sample_type(self, type_name: str, payload: dict[str, Any]) -> SampleTypeDTO:
        sample_type = self.sample_type_repository.get_by_name(type_name)
        if sample_type is None:
            raise NotFoundError(f"Sample type '{type_name}' not found")
        if "type_name" in payload:
            sample_type.type_name = payload["type_name"]
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(sample_type)

    def delete_sample_type(self, type_name: str) -> None:
        sample_type = self.sample_type_repository.get_by_name(type_name)
        if sample_type is None:
            raise NotFoundError(f"Sample type '{type_name}' not found")
        self.uow.session.delete(sample_type)

    def _validate_create(self, payload: dict[str, Any]) -> SampleTypeDTO:
        if "type_name" not in payload:
            raise ServiceValidationError("Missing required field: type_name")
        type_name = payload["type_name"]
        if not isinstance(type_name, str) or not type_name.strip():
            raise ServiceValidationError("Type name must be a non-empty string")
        return SampleTypeDTO(type_name=type_name)

    def _dto_to_model(self, dto: SampleTypeDTO):
        from server.persistence.models.sample_type import SampleType as SampleTypeModel
        return SampleTypeModel(type_name=dto.type_name)

    def _to_dto(self, sample_type) -> SampleTypeDTO:
        return SampleTypeDTO(
            id=sample_type.id,
            type_name=sample_type.type_name,
            last_update=sample_type.last_update,
        )
