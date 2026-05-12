from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Date, DateTime, func
from datetime import date, datetime
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .sample import Sample

# ==== PATIENT ====
# Relationships ->
#   1:N → Sample (one patient has many samples)
class Patient(Base):
    __tablename__="patient" 
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True) 
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    registration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    test: Mapped[str] = mapped_column(String(50), nullable= False)
    # Sample relationship
    samples: Mapped[list["Sample"]] = relationship(back_populates="patient")