# Python standard library
from datetime import date, datetime
from typing import TYPE_CHECKING

# SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Date, ForeignKey, UniqueConstraint, func, Column, DateTime

# Internal - database
from ..database import Base

if TYPE_CHECKING:
    from .sample import Sample
    from .research_project import ResearchProject

# === SAMPLES IN RESEARCH PROJECT ===
# Relationships ->
#   N:1 → Sample
#   N:1 → ResearchProject
class ResearchProjectSamples(Base):
    __tablename__="research_project_samples"
    __table_args__ = (UniqueConstraint("id_sample", "id_project", name="uq_sample_project"),)
    sample_assignment_date: Mapped[date] = mapped_column(DateTime, nullable=False, server_default=func.now())
    id_sample: Mapped[int] = mapped_column(ForeignKey("sample.id", ondelete="CASCADE"), primary_key=True)
    id_project: Mapped[int] = mapped_column(ForeignKey("research_project.id", ondelete="CASCADE"), primary_key=True)
    sample: Mapped["Sample"] = relationship(overlaps="research_projects,samples")
    project: Mapped["ResearchProject"] = relationship(overlaps="research_projects,samples")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )