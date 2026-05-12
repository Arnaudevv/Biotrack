# Python standard library
from typing import Optional

# SQLAlchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

# Internal - models
from ..models import Patient

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# PATIENT REPOSITORY
# ══════════════════════════════════════════════════════════════════

class PatientRepository(BaseRepository[Patient]):
    """
    Repository for the Patient table.
    Inherits get_by_id, get_all, save, delete and count from BaseRepository.
    Adds Patient-specific methods.
    """

    def __init__(self, session: Session):
        # Tell the parent which model we are working with
        super().__init__(session, Patient)

    def get_by_code(self, code: str) -> Optional[Patient]:
        """
        Finds a patient by their unique code (e.g. "P001").
        Returns None if not found.

        Example  ->  patient = repo.get_by_code("P001")
        """
        stmt = select(Patient).where(Patient.code == code)
        return self.session.scalar(stmt)

    def get_active(self) -> list[Patient]:
        """
        Returns all patients where active=True.

        Example -> active = repo.get_active()
        """
        stmt = select(Patient).where(Patient.active == True).order_by(Patient.lastname)
        return self.session.scalars(stmt).all()

    def get_with_samples(self, code: str) -> Optional[Patient]:
        """
        Finds a patient AND eagerly loads their samples in the same query.
        This allows accessing patient.samples outside the session without error.

        Without this method, accessing patient.samples outside 'with Session()'
        would raise a DetachedInstanceError.

        Example:
            patient = repo.get_with_samples("P001")
            for sample in patient.samples:
                print(sample.code)
        """
        stmt = (
            select(Patient)
            .where(Patient.code == code)
            .options(selectinload(Patient.samples))  # eagerly load samples
        )
        return self.session.scalar(stmt)