"""Business logic for research project resources."""

from __future__ import annotations

from datetime import date
from typing import Any

from server.persistence.models.project_team import ProjectTeam
from server.persistence.repositories.research_project_repository import ResearchProjectRepository
from server.persistence.repositories.sample_repository import SampleRepository
from server.persistence.repositories.staff_repository import StaffRepository
from server.persistence.repositories.unit_of_work import AbstractUnitOfWork
from shared.dtos import ProjectDTO
from shared.errors import ConflictError, NotFoundError, ServiceValidationError


class ProjectService:
    """Manage research project records and assignments."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.project_repository = ResearchProjectRepository(uow.session)
        self.sample_repository = SampleRepository(uow.session)
        self.staff_repository = StaffRepository(uow.session)

    def list_projects(self, name: str | None = None) -> list[ProjectDTO]:
        if name:
            project = self.project_repository.get_by_name(name)
            return [self._to_dto(project)] if project is not None else []
        records = self.project_repository.get_all()
        return [self._to_dto(record) for record in records]

    def get_project(self, project_id: int) -> ProjectDTO:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        return self._to_dto(project)

    def create_project(self, payload: dict[str, Any]) -> ProjectDTO:
        dto = self._validate_create(payload)
        if self.project_repository.get_by_name(dto.project_name) is not None:
            raise ConflictError(f"Project '{dto.project_name}' already exists")
        project = self._dto_to_model(dto)
        self.uow.session.add(project)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(project)

    def update_project(self, project_id: int, payload: dict[str, Any]) -> ProjectDTO:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        for field in ("project_name", "start_date", "description"):
            if field in payload:
                value = payload[field]
                if field == "start_date":
                    setattr(project, field, self._parse_date(value, field))
                else:
                    setattr(project, field, value)
        try:
            self.uow.session.flush()
        except Exception as exc:
            raise ConflictError(str(exc)) from exc
        return self._to_dto(project)

    def delete_project(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        self.uow.session.delete(project)

    def add_sample_to_project(self, project_id: int, sample_code: str) -> dict[str, Any]:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        sample = self.sample_repository.get_by_code(sample_code)
        if sample is None:
            raise NotFoundError(f"Sample '{sample_code}' not found")
        if any(item.code == sample_code for item in project.samples):
            raise ConflictError(f"Sample '{sample_code}' already associated with project '{project_id}'")
        project.samples.append(sample)
        self.uow.session.flush()
        return {"project_id": project.id, "sample_code": sample.code}

    def add_team_member(self, project_id: int, staff_code: str, role: str) -> dict[str, Any]:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        staff = self.staff_repository.get_by_code(staff_code)
        if staff is None:
            raise NotFoundError(f"Staff '{staff_code}' not found")
        valid_roles = {"principal_investigator", "co_investigator", "analyst", "technician", "assistant"}
        role = str(role).strip().lower()
        if role not in valid_roles:
            raise ServiceValidationError("Role must be a valid project role")
        if any(member.id == staff.id for member in project.staff_members):
            raise ConflictError(f"Staff '{staff_code}' is already on project '{project_id}'")
        team_member = ProjectTeam(id_project=project.id, id_staff=staff.id, role=role)
        self.uow.session.add(team_member)
        self.uow.session.flush()
        return {"project_id": project.id, "staff_code": staff.code, "role": role}

    def _validate_create(self, payload: dict[str, Any]) -> ProjectDTO:
        required = ["project_name", "start_date"]
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                raise ServiceValidationError(f"Missing required field: {field}")
        project_name = payload["project_name"]
        if not isinstance(project_name, str):
            raise ServiceValidationError("Project name must be a string")
        start_date = self._parse_date(payload["start_date"], "start_date")
        return ProjectDTO(
            project_name=project_name,
            start_date=start_date,
            description=payload.get("description"),
        )

    def _parse_date(self, value: Any, field_name: str) -> date:
        if isinstance(value, date) and not isinstance(value, str):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ServiceValidationError(f"Invalid {field_name}: {value}") from exc
        raise ServiceValidationError(f"Invalid {field_name}: {value}")

    def _dto_to_model(self, dto: ProjectDTO):
        from server.persistence.models.research_project import ResearchProject as ResearchProjectModel
        return ResearchProjectModel(
            project_name=dto.project_name,
            start_date=dto.start_date,
            description=dto.description,
        )

    def _to_dto(self, project) -> ProjectDTO:
        return ProjectDTO(
            id=project.id,
            project_name=project.project_name,
            start_date=project.start_date,
            description=project.description,
        )
