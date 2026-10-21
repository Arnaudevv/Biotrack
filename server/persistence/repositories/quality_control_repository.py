# Python standard library
from typing import Optional

# SQLAlchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

# Internal - models
from ..models import QualityControl, Sample

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# QUALITY CONTROL REPOSITORY
# ══════════════════════════════════════════════════════════════════

class QualityControlRepository(BaseRepository[QualityControl, int]):
    """
    Repository for the QualityControl table.
    Inherits get_by_id, get_all, save, delete and count from BaseRepository.
    Adds QualityControl-specific methods.

    Note: QualityControl has a 1:1 relationship with Sample (one record per sample).
    """

    def __init__(self, session: Session):
        super().__init__(session, QualityControl)

    # ── Lookup by related entity ──────────────────────────────────

    def get_by_sample_code(self, sample_code: str) -> Optional[QualityControl]:
        """
        Finds the quality control record associated with the given sample code.
        Returns None if the sample has no QC record yet.
        Performs a JOIN with the Sample table.

        Example:
            qc = repo.get_by_sample_code("SMP-001")
            if qc:
                print(qc.result, qc.purity, qc.concentration)
        """
        stmt = (
            select(QualityControl)
            .join(Sample, Sample.id == QualityControl.id_sample)
            .where(Sample.code == sample_code)
        )
        return self.session.scalar(stmt)

    # ── Lookup by field ───────────────────────────────────────────

    def get_by_result(self, result: str) -> list[QualityControl]:
        """
        Returns all QC records matching the given result.
        Valid values: 'approved', 'rejected', 'pending_review'.

        Example:
            rejected = repo.get_by_result("rejected")
            print(f"{len(rejected)} samples failed quality control")
        """
        stmt = select(QualityControl).where(QualityControl.result == result)
        return list(self.session.scalars(stmt).all())

    def get_below_purity(self, threshold: float) -> list[QualityControl]:
        """
        Returns all QC records where purity is below the given threshold.
        Useful for identifying low-quality samples.
        Skips records where purity is NULL.

        Example:
            low_purity = repo.get_below_purity(80.0)
            for qc in low_purity:
                print(f"Sample id {qc.id_sample}: purity {qc.purity}%")
        """
        stmt = select(QualityControl).where(
            QualityControl.purity != None,
            QualityControl.purity < threshold,
        )
        return list(self.session.scalars(stmt).all())

    # ── Eager loading ─────────────────────────────────────────────

    def get_with_sample(self, qc_id: int) -> Optional[QualityControl]:
        """
        Finds a QC record by its id AND eagerly loads the associated sample.
        Useful when you need to access qc.sample outside the session.

        Example:
            qc = repo.get_with_sample(5)
            if qc:
                print(qc.result, qc.sample.code)
        """
        stmt = (
            select(QualityControl)
            .where(QualityControl.id == qc_id)
            .options(selectinload(QualityControl.sample))
        )
        return self.session.scalar(stmt)