from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Enum
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .protocol import Protocol
    from .research_project import ResearchProject

# === STAFF ====
# Relationships ->
#   1:N → Protocol (one staff member has reviewed many protocols)
#   N:M → ResearchProject through ProjectTeam (a staff member can be part of many projects)
class Staff(Base):
    __tablename__="staff"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True) 
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(Enum('researcher','analyst','technician','manager','administrator'), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Protocol relationship
    protocols: Mapped[list["Protocol"]] = relationship(back_populates="staff")
    research_projects: Mapped[list["ResearchProject"]] = relationship(secondary="project_team", back_populates="staff_members")