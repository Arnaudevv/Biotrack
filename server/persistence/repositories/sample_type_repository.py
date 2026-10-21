# Python standard library
from typing import Optional

# SQLAlchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

# Internal - models
from ..models import SampleType

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# SAMPLE TYPE REPOSITORY
# ══════════════════════════════════════════════════════════════════

class SampleTypeRepository(BaseRepository[SampleType, int]):
    """
    Repository for the SampleType table.
    Inherits get_by_id, get_all, save, delete and count from BaseRepository.
    Adds SampleType-specific methods.
    """

    def __init__(self, session: Session):
        super().__init__(session, SampleType)

    # ── Lookup by field ───────────────────────────────────────────

    def get_by_name(self, type_name: str) -> Optional[SampleType]:
        """
        Finds a sample type by its unique name (e.g. "Blood", "Urine").
        Returns None if not found.

        Example:
            sample_type = repo.get_by_name("Blood")
        """
        stmt = select(SampleType).where(SampleType.type_name == type_name)
        return self.session.scalar(stmt)

    # ── Eager loading ─────────────────────────────────────────────

    def get_with_samples(self, type_name: str) -> Optional[SampleType]:
        """
        Finds a sample type AND eagerly loads all samples of that type.
        Useful when you need to access sample_type.samples outside the session.

        Example:
            sample_type = repo.get_with_samples("Blood")
            for sample in sample_type.samples:
                print(sample.code)
        """
        stmt = (
            select(SampleType)
            .where(SampleType.type_name == type_name)
            .options(selectinload(SampleType.samples))
        )
        return self.session.scalar(stmt)