from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Numeric, Enum, ForeignKey, CheckConstraint
from ..database import Base

# The models reference each other (e.g., Sample ↔ LogTemperature), which would cause
# circular imports if they were imported directly. TYPE_CHECKING is False at runtime
# (the imports are not executed), but True for the type checker, so the IDE
# resolves the types correctly without breaking the application.
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .sample import Sample


# === QUALITY CONTROL ===
# Relationships ->
#   1:1 → Sample (a quality control record belongs to a single sample)
class QualityControl(Base):
    __tablename__="quality_control"
    __table_args__ = (
        CheckConstraint("purity BETWEEN 0 AND 100", name="check_purity_range"),
        CheckConstraint("concentration >= 0", name="check_concentration_positive")
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purity: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    concentration: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    result: Mapped[str] = mapped_column(Enum('approved', 'rejected', 'pending_review'), nullable=False)
    #FK - quality_control - sample
    id_sample: Mapped[int] = mapped_column(ForeignKey("sample.id", ondelete="CASCADE"), nullable=False, unique=True)
    sample: Mapped["Sample"] = relationship(back_populates="quality_control", uselist=False)