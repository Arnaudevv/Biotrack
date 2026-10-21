# Python standard library
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

# SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Date, func, Column, DateTime

# Internal - database
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
if TYPE_CHECKING:
    from .sample import Sample
    from .staff import Staff


# === RESEARCH PROJECT ===
# Relationships ->
#   N:M → Sample through ResearchProjectSamples (one project has many samples and vice versa)
#   N:M → Staff through ProjectTeam (one project has many staff members and vice versa)
class  ResearchProject(Base):
    __tablename__="research_project"
    id:  Mapped[int] = mapped_column(Integer, primary_key=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # research_project_samples relationship
    samples: Mapped[list["Sample"]] = relationship(secondary="research_project_samples", back_populates="research_projects")
    # project_team relationship
    staff_members: Mapped[list["Staff"]] = relationship(secondary="project_team", back_populates="research_projects")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )