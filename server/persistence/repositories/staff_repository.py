# Python standard library
from typing import Optional

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy import select

# Internal - models
from ..models import Staff, ResearchProject, ProjectTeam

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# STAFF REPOSITORY
# ══════════════════════════════════════════════════════════════════

class StaffRepository(BaseRepository[Staff, int]):
    """Repository for the Staff table."""

    def __init__(self, session: Session):
        # Tell the parent which model we are working with
        super().__init__(session, Staff)

    def get_by_code(self, code: str) -> Optional[Staff]:
        """
        Finds a staff member by their unique code (e.g. "S001").

        Example  -> staff = repo.get_by_code("S001")
        """
        stmt = select(Staff).where(Staff.code == code)
        return self.session.scalar(stmt)

    def add_to_research_project(self, code: str, project_name: str, role: str):
        staff = self.session.scalar(
            select(Staff).
            where(Staff.code == code)
        )

        project = self.session.scalar(
            select(ResearchProject)
            .where((ResearchProject.project_name) == project_name)
        )

        if not staff:
            raise ValueError(f"Staff [{code}] not found")

        if not project:
            raise ValueError(f"Project [{project_name}] not found")

        new_assignment = ProjectTeam(
            id_staff=staff.id,
            id_project=project.id,
            role=role.strip().lower()
        )

        self.session.add(new_assignment)

    def get_research_project_with_roles(self, code: str) -> list[ProjectTeam]:
        """
        Retrieves research project assignments for a given staff code.

        Returns a list of ProjectTeam objects if found, otherwise an empty list.

        Example:
            assignments = repo.get_research_project_with_roles("STF-001")
            for assignment in assignments:
                print(f"Project: {assignment.project.project_name}, Role: {assignment.role}")
        """
        stmt = (
            select(ProjectTeam)
            .join(Staff, Staff.id == ProjectTeam.id_staff)
            .where(Staff.code == code)
        )

        return list(self.session.scalars(stmt).all())