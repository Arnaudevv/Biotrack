from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .sample import Sample


# === SAMPLE TYPE ===
# Relationships ->
#   1:N → Sample (one type can be applied to many samples)
class SampleType(Base):
    __tablename__="sample_type"
    id:  Mapped[int] = mapped_column(Integer, primary_key=True)
    type_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # Sample relationship
    samples: Mapped[list["Sample"]] = relationship(back_populates="sample_type")