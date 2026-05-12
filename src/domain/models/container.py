# Python standard library
from __future__ import annotations
from datetime import datetime 
from typing import TYPE_CHECKING

# SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, func, Column

# Internal - database
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
if TYPE_CHECKING:
    from .sample import Sample


# === SAMPLE CONTAINER ===
# Relationships ->
#   1:N → Sample (one container can store many samples)
class Container(Base):
    __tablename__="container"
    id:  Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True) 
    type_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # Sample relationship
    samples: Mapped[list["Sample"]] = relationship(back_populates="container")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )