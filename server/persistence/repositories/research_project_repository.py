# Python standard library
from typing import Optional

# SQLAlchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

# Internal - models
from ..models import ResearchProject, ResearchProjectSamples, ProjectTeam, Staff

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# RESEARCH PROJECT REPOSITORY
# ══════════════════════════════════════════════════════════════════

class ResearchProjectRepository(BaseRepository[ResearchProject, int]):
    """
    Repository for the ResearchProject table.
    """

    def __init__(self, session: Session):
        super().__init__(session, ResearchProject)

    def get_by_name(self, name: str) -> Optional[ResearchProject]:
        """
        Finds a project by its exact name.

        Example:
            project = repo.get_by_name("Oncology Study Alpha")
        """
        stmt = select(ResearchProject).where(ResearchProject.project_name == name)
        return self.session.scalar(stmt)

    def search_by_name(self, keyword: str) -> list[ResearchProject]:
        """Find projects whose names contain the keyword, case-insensitively."""
        stmt = select(ResearchProject).where(ResearchProject.project_name.ilike(f"%{keyword}%"))
        return list(self.session.scalars(stmt).all())

    def get_with_team(self, project_id: int) -> Optional[ResearchProject]:
        """
        Finds a project AND eagerly loads its team (staff) and samples.

        Example:
            project = repo.get_with_team(1)
            for member in project.staff_members:
                print(member.name, member.role)
            for sample in project.samples:
                print(sample.code)
        """
        stmt = (
            select(ResearchProject)
            .where(ResearchProject.id == project_id)
            .options(
                selectinload(ResearchProject.staff_members),
                selectinload(ResearchProject.samples),
            )
        )
        return self.session.scalar(stmt)

    def get_sample_assignment(self, project_id: int, sample_id: int) -> Optional[ResearchProjectSamples]:
        stmt = select(ResearchProjectSamples).where(
            ResearchProjectSamples.id_project == project_id,
            ResearchProjectSamples.id_sample == sample_id,
        )
        return self.session.scalar(stmt)

    def get_team_assignment(self, project_id: int, staff_id: int) -> Optional[ProjectTeam]:
        stmt = select(ProjectTeam).where(
            ProjectTeam.id_project == project_id,
            ProjectTeam.id_staff == staff_id,
        )
        return self.session.scalar(stmt)

    def get_team(self, project_id: int) -> list[ProjectTeam]:
        stmt = (
            select(ProjectTeam)
            .where(ProjectTeam.id_project == project_id)
            .options(selectinload(ProjectTeam.staff))
        )
        return list(self.session.scalars(stmt).all())