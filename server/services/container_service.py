"""Business logic for container resources."""

from __future__ import annotations

from typing import Any

from server.persistence.repositories.container_repository import ContainerRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import ContainerDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class ContainerService:
    """Manage containers used to store samples."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.container_repository = ContainerRepository(uow.session)

    def list_containers(self) -> list[ContainerDTO]:
        return [self._to_dto(record) for record in self.container_repository.get_all()]

    def get_container(self, code: str) -> ContainerDTO:
        container = self.container_repository.get_by_code(code)
        if container is None:
            raise NotFoundError(f"Container '{code}' not found")
        return self._to_dto(container)

    def create_container(self, payload: dict[str, Any]) -> ContainerDTO:
        dto = self._validate_create(payload)
        if self.container_repository.get_by_code_or_type_name(dto.code, dto.type_name) is not None:
            raise ConflictError(f"Container '{dto.code}' or type '{dto.type_name}' already exists")
        container = self._dto_to_model(dto)
        self.uow.session.add(container)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(container)

    def update_container(self, code: str, payload: dict[str, Any]) -> ContainerDTO:
        container = self.container_repository.get_by_code(code)
        if container is None:
            raise NotFoundError(f"Container '{code}' not found")
        if "type_name" in payload:
            container.type_name = payload["type_name"]
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(container)

    def delete_container(self, code: str) -> None:
        container = self.container_repository.get_by_code(code)
        if container is None:
            raise NotFoundError(f"Container '{code}' not found")
        self.uow.session.delete(container)

    def _validate_create(self, payload: dict[str, Any]) -> ContainerDTO:
        if "code" not in payload or "type_name" not in payload:
            raise ServiceValidationError("Missing required fields: code, type_name")
        code = payload["code"]
        type_name = payload["type_name"]
        if not isinstance(code, str) or not code.strip():
            raise ServiceValidationError("Code must be a non-empty string")
        if not isinstance(type_name, str) or not type_name.strip():
            raise ServiceValidationError("Type name must be a non-empty string")
        return ContainerDTO(code=code, type_name=type_name)

    def _dto_to_model(self, dto: ContainerDTO):
        from server.persistence.models.container import Container as ContainerModel
        return ContainerModel(code=dto.code, type_name=dto.type_name)

    def _to_dto(self, container) -> ContainerDTO:
        return ContainerDTO(
            id=container.id,
            code=container.code,
            type_name=container.type_name,
            last_update=container.last_update,
        )
