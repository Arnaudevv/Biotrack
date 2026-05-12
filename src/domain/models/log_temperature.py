from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Numeric, DateTime, ForeignKey, func, Column
from datetime import datetime
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .sample import Sample


# === RECORDED TEMPERATURES ===
# Relationships ->
#   N:1 → Sample (a temperature record belongs to a sample)
class LogTemperature(Base):
    __tablename__="log_temperature"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reading_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    temperature: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    #FK log_temp - sample
    id_sample: Mapped[int] = mapped_column(ForeignKey("sample.id", ondelete="CASCADE"), nullable=False)
    sample: Mapped["Sample"] = relationship(back_populates="log_temperatures")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )