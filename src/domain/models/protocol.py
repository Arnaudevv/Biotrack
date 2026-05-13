# Python standard library
from __future__ import annotations
from datetime import date
from typing import Optional, TYPE_CHECKING


# SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer, String, Text, Date, LargeBinary, 
    ForeignKey, func, Column, DateTime
)

# Internal - database
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
if TYPE_CHECKING:
    from .association_tables import sample_protocol
    from .staff import Staff
    from .sample import Sample


# === PROTOCOL ===
# Relationships ->
#   N:1 → Staff (one protocol is reviewed by a staff member)
#   N:M → Sample through SampleProtocol (one protocol can be applied to many samples)
class Protocol(Base):
    __tablename__="protocol"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    protocol_file: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    creation_date: Mapped[date] = mapped_column(DateTime, nullable=False, server_default=func.now())
    last_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # FK: protocol - staff
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    staff: Mapped[Optional["Staff"]] = relationship(back_populates="protocols")
    # sample_protocol relationship
    samples: Mapped[list["Sample"]] = relationship(secondary="sample_protocol", back_populates="protocols")
    
    last_update = Column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )