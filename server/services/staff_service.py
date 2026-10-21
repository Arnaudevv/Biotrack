"""Business logic for staff resources."""

from __future__ import annotations

from typing import Any

from server.persistence.repositories.staff_repository import StaffRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import StaffDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class StaffService:
    """Manage staff records and validation rules."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.staff_repository = StaffRepository(uow.session)

    def list_staff(self) -> list[StaffDTO]:
        return [self._to_dto(record) for record in self.staff_repository.get_all()]

    def get_staff(self, code: str) -> StaffDTO:
        staff = self.staff_repository.get_by_code(code)
        if staff is None:
            raise NotFoundError(f"Staff '{code}' not found")
        return self._to_dto(staff)

    def list_assignments(self, code: str) -> list[dict[str, Any]]:
        staff = self.staff_repository.get_by_code(code)
        if staff is None:
            raise NotFoundError(f"Staff '{code}' not found")
        assignments = self.staff_repository.get_research_project_with_roles(code)
        payload = []
        for assignment in assignments:
            payload.append({
                "project_id": assignment.project.id,
                "project_name": assignment.project.project_name,
                "role": assignment.role,
            })
        return payload

    def create_staff(self, payload: dict[str, Any]) -> StaffDTO:
        dto = self._validate_create(payload)
        if self.staff_repository.get_by_code(dto.code) is not None:
            raise ConflictError(f"Staff '{dto.code}' already exists")
        staff = self._dto_to_model(dto)
        self.uow.session.add(staff)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(staff)

    def update_staff(self, code: str, payload: dict[str, Any]) -> StaffDTO:
        staff = self.staff_repository.get_by_code(code)
        if staff is None:
            raise NotFoundError(f"Staff '{code}' not found")
        for field in ("name", "lastname", "role"):
            if field in payload:
                value = payload[field]
                if field == "role":
                    role = value.strip().lower()
                    self._validate_role(role)
                    setattr(staff, field, role)
                else:
                    setattr(staff, field, value)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(staff)

    def delete_staff(self, code: str) -> None:
        staff = self.staff_repository.get_by_code(code)
        if staff is None:
            raise NotFoundError(f"Staff '{code}' not found")
        self.uow.session.delete(staff)

    def _validate_create(self, payload: dict[str, Any]) -> StaffDTO:
        required = ["code", "name", "lastname", "role"]
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                raise ServiceValidationError(f"Missing required field: {field}")
        if not isinstance(payload["code"], str):
            raise ServiceValidationError("Code must be a string")
        if not isinstance(payload["name"], str) or not isinstance(payload["lastname"], str):
            raise ServiceValidationError("Name and lastname must be strings")
        role = str(payload["role"]).strip().lower()
        self._validate_role(role)
        return StaffDTO(
            code=payload["code"],
            name=payload["name"],
            lastname=payload["lastname"],
            role=role,
            active=bool(payload.get("active", True)),
        )

    def _validate_role(self, role: str) -> None:
        allowed = {"researcher", "analyst", "technician", "manager", "administrator"}
        if role not in allowed:
            raise ServiceValidationError(f"Role must be one of: {', '.join(sorted(allowed))}")

    def _dto_to_model(self, dto: StaffDTO):
        from server.persistence.models.staff import Staff as StaffModel
        return StaffModel(
            code=dto.code,
            name=dto.name,
            lastname=dto.lastname,
            role=dto.role,
            active=dto.active,
        )

    def _to_dto(self, staff) -> StaffDTO:
        return StaffDTO(
            id=staff.id,
            code=staff.code,
            name=staff.name,
            lastname=staff.lastname,
            role=staff.role,
            active=bool(staff.active),
        )
