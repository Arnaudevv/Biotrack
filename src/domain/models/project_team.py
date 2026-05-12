# Python standard library
from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING


# SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Enum, ForeignKey, Column, func, DateTime

# Internal - database
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
if TYPE_CHECKING:
    from .research_project import ResearchProject
    from .staff import Staff


# === PROJECT TEAM (staff - research project) ===
# Relationships ->
#   N:1 → ResearchProject
#   N:1 → Staff
class ProjectTeam(Base):
    __tablename__="project_team"
    id_project: Mapped[int] = mapped_column(ForeignKey("research_project.id", ondelete="CASCADE"), primary_key=True)
    id_staff: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(Enum('principal_investigator','co_investigator','analyst','technician','assistant'), nullable=False)
    
    # added (04/05/2026) -> this allows to get ResearchProject and Staff Objects using repositoryies
    project: Mapped["ResearchProject"] = relationship(overlaps="research_projects,staff_members")
    staff: Mapped["Staff"] = relationship(overlaps="research_projects,staff_members")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )