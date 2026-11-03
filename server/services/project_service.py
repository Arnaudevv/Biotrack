"""Business logic for research project resources."""

from __future__ import annotations

from datetime import date
from typing import Any

from server.persistence.models.project_team import ProjectTeam
from server.persistence.models.research_project_samples import ResearchProjectSamples
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
            return [self._to_dto(project) for project in self.project_repository.search_by_name(name)]
        records = self.project_repository.get_all()
        return [self._to_dto(record) for record in records]

    def get_project(self, project_id: int) -> ProjectDTO:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        return self._to_dto(project)

    def get_project_details(self, project_id: int) -> dict[str, Any]:
        project = self.project_repository.get_with_team(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        from server.persistence.models.project_team import ProjectTeam
        from server.persistence.models.research_project_samples import ResearchProjectSamples
        team_rows = self.uow.session.query(ProjectTeam).filter_by(id_project=project_id).all()
        sample_rows = self.uow.session.query(ResearchProjectSamples).filter_by(id_project=project_id).all()
        return {
            "id": project.id,
            "project_name": project.project_name,
            "start_date": project.start_date.isoformat(),
            "description": project.description,
            "team": [
                {"staff_code": member.staff.code, "name": f"{member.staff.name} {member.staff.lastname}".strip(),
                 "role": member.role}
                for member in team_rows
            ],
            "samples": [
                {"sample_code": row.sample.code, "sample_assignment_date": row.sample_assignment_date.isoformat()}
                for row in sample_rows
            ],
        }

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
                elif field == "project_name":
                    if self.project_repository.get_by_name(value) not in (None, project):
                        raise ConflictError(f"Project '{value}' already exists")
                    setattr(project, field, value)
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

    def add_sample_to_project(
        self, project_id: int, sample_code: str, assignment_date: Any = None
    ) -> dict[str, Any]:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        sample = self.sample_repository.get_by_code(sample_code)
        if sample is None:
            raise NotFoundError(f"Sample '{sample_code}' not found")
        if any(item.code == sample_code for item in project.samples):
            raise ConflictError(f"Sample '{sample_code}' already associated with project '{project_id}'")
        parsed_date = date.today() if assignment_date is None else self._parse_date(
            assignment_date, "sample_assignment_date"
        )
        if parsed_date > date.today():
            raise ServiceValidationError("Sample assignment date cannot be in the future")
        self.uow.session.add(ResearchProjectSamples(
            id_project=project.id,
            id_sample=sample.id,
            sample_assignment_date=parsed_date,
        ))
        self.uow.session.flush()
        return {
            "project_id": project.id,
            "sample_code": sample.code,
            "sample_assignment_date": parsed_date.isoformat(),
        }

    def list_project_samples(self, project_id: int) -> list[dict[str, Any]]:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        rows = self.uow.session.query(ResearchProjectSamples).filter_by(id_project=project_id).all()
        return [{"sample_code": row.sample.code, "sample_assignment_date": row.sample_assignment_date.isoformat()} for row in rows]

    def update_sample_assignment(self, project_id: int, sample_code: str, assignment_date: Any) -> dict[str, Any]:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        sample = self.sample_repository.get_by_code(sample_code)
        if sample is None:
            raise NotFoundError(f"Sample '{sample_code}' not found")
        assignment = self.project_repository.get_sample_assignment(project_id, sample.id)
        if assignment is None:
            raise NotFoundError(f"Sample '{sample_code}' is not linked to project '{project_id}'")
        parsed = self._parse_date(assignment_date, "sample_assignment_date")
        if parsed > date.today():
            raise ServiceValidationError("Sample assignment date cannot be in the future")
        assignment.sample_assignment_date = parsed
        return {"project_id": project_id, "sample_code": sample_code, "sample_assignment_date": parsed.isoformat()}

    def remove_sample_from_project(self, project_id: int, sample_code: str) -> None:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        sample = self.sample_repository.get_by_code(sample_code)
        if sample is None:
            raise NotFoundError(f"Sample '{sample_code}' not found")
        assignment = self.project_repository.get_sample_assignment(project_id, sample.id)
        if assignment is None:
            raise NotFoundError(f"Sample '{sample_code}' is not linked to project '{project_id}'")
        self.uow.session.delete(assignment)

    def add_team_member(self, project_id: int, staff_code: str, role: str) -> dict[str, Any]:
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        staff = self.staff_repository.get_by_code(staff_code)
        if staff is None:
            raise NotFoundError(f"Staff '{staff_code}' not found")
        if not staff.active:
            raise ServiceValidationError(f"Staff '{staff_code}' is inactive")
        valid_roles = {"principal_investigator", "co_investigator", "analyst", "technician", "assistant"}
        role = str(role).strip().lower()
        if role not in valid_roles:
            raise ServiceValidationError("Role must be a valid project role")
        if any(member.id == staff.id for member in project.staff_members):
            raise ConflictError(f"Staff '{staff_code}' is already on project '{project_id}'")
        if role == "principal_investigator" and any(
            assignment.role == "principal_investigator"
            for assignment in self.project_repository.get_team(project_id)
        ):
            raise ConflictError(f"Project '{project_id}' already has a principal investigator")
        team_member = ProjectTeam(id_project=project.id, id_staff=staff.id, role=role)
        self.uow.session.add(team_member)
        self.uow.session.flush()
        return {"project_id": project.id, "staff_code": staff.code, "role": role}

    def list_project_team(self, project_id: int) -> list[dict[str, Any]]:
        if self.project_repository.get_by_id(project_id) is None:
            raise NotFoundError(f"Project '{project_id}' not found")
        return [{"staff_code": row.staff.code, "name": f"{row.staff.name} {row.staff.lastname}".strip(), "role": row.role} for row in self.project_repository.get_team(project_id)]

    def update_team_member(self, project_id: int, staff_code: str, role: str) -> dict[str, Any]:
        staff = self.staff_repository.get_by_code(staff_code)
        if staff is None:
            raise NotFoundError(f"Staff '{staff_code}' not found")
        assignment = self.project_repository.get_team_assignment(project_id, staff.id)
        if assignment is None:
            raise NotFoundError(f"Staff '{staff_code}' is not assigned to project '{project_id}'")
        role = str(role).strip().lower()
        valid_roles = {"principal_investigator", "co_investigator", "analyst", "technician", "assistant"}
        if role not in valid_roles:
            raise ServiceValidationError("Role must be a valid project role")
        if role == "principal_investigator" and any(
            row.role == role and row.id_staff != staff.id
            for row in self.project_repository.get_team(project_id)
        ):
            raise ConflictError(f"Project '{project_id}' already has a principal investigator")
        assignment.role = role
        return {"project_id": project_id, "staff_code": staff_code, "role": role}

    def remove_team_member(self, project_id: int, staff_code: str) -> None:
        staff = self.staff_repository.get_by_code(staff_code)
        if staff is None:
            raise NotFoundError(f"Staff '{staff_code}' not found")
        assignment = self.project_repository.get_team_assignment(project_id, staff.id)
        if assignment is None:
            raise NotFoundError(f"Staff '{staff_code}' is not assigned to project '{project_id}'")
        self.uow.session.delete(assignment)

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
            last_update=project.last_update,
        )
