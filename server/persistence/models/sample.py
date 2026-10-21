# Python standard library
from datetime import date
from typing import TYPE_CHECKING

# SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer, String, Numeric, Date, Enum, ForeignKey, 
    CheckConstraint, func, Column, DateTime
)

# Internal - database
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
if TYPE_CHECKING:
    from .patient import Patient
    from .sample_type import SampleType
    from .container import Container
    from .log_temperature import LogTemperature
    from .quality_control import QualityControl
    from .protocol import Protocol
    from .association_tables import sample_protocol
    from .research_project import ResearchProject

# === SAMPLE ===
# Relationships ->
#   N:1 → Patient (a sample belongs to a patient)
#   N:1 → SampleType (a sample has a type)
#   N:1 → Container (a sample is stored in a container)
#   1:N → LogTemperature (a sample has many temperature records)
#   1:1 → QualityControl (a sample has a single quality control record)
#   N:M → Protocol through SampleProtocol (a sample can follow many protocols)
#   N:M → ResearchProject through ResearchProjectSamples (a sample can be part of many projects)
class Sample(Base):
    __tablename__="sample"
    __table_args__ = (CheckConstraint("volume > 0", name="check_volume_positive"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    volume: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    extraction_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Enum('pending','in_process','analyzed','rejected','archived'), nullable=False, default='pending')
    # FK: sample - patient
    id_patient: Mapped[int] = mapped_column(ForeignKey("patient.id"), nullable=False)
    patient: Mapped["Patient"] = relationship(back_populates="samples") 
    # FK: sample - sample type
    id_sample_type: Mapped[int] = mapped_column(ForeignKey("sample_type.id"), nullable=False)
    sample_type: Mapped["SampleType"] = relationship(back_populates="samples")
    #FK: sample - container
    id_container: Mapped[int] = mapped_column(ForeignKey("container.id"), nullable=False)
    container: Mapped["Container"] = relationship(back_populates="samples")
    # log_temperatures relationship
    log_temperatures: Mapped[list["LogTemperature"]] = relationship(back_populates="sample")
    # quality_control relationship
    quality_control: Mapped["QualityControl"] = relationship(back_populates="sample", uselist=False)
    # sample_protocol relationship
    protocols: Mapped[list["Protocol"]] = relationship(secondary="sample_protocol", back_populates="samples")
    # research_project_samples relationship
    research_projects: Mapped[list["ResearchProject"]] = relationship(secondary="research_project_samples", back_populates="samples")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )