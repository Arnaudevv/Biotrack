# Python standard library
from typing import Optional
from datetime import date

# SQLAlchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

# Internal - models
from ..models import Sample, Patient, SampleType, Container

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# SAMPLE REPOSITORY
# ══════════════════════════════════════════════════════════════════

class SampleRepository(BaseRepository[Sample, int]):
    """
    Repository for the Sample table.
    Inherits get_by_id, get_all, save, delete and count from BaseRepository.
    Adds Sample-specific methods.
    """

    def __init__(self, session: Session):
        super().__init__(session, Sample)

    # ── Lookup by field ───────────────────────────────────────────

    def get_by_code(self, code: str) -> Optional[Sample]:
        """
        Finds a sample by its unique code (e.g. "SMP-001").
        Returns None if not found.

        Example:
            sample = repo.get_by_code("SMP-001")
        """
        stmt = select(Sample).where(Sample.code == code)
        return self.session.scalar(stmt)

    def get_by_status(self, status: str) -> list[Sample]:
        """
        Returns all samples with the given status.
        Valid values: 'pending', 'in_process', 'analyzed', 'rejected', 'archived'.

        Example:
            pending = repo.get_by_status("pending")
            for sample in pending:
                print(sample.code)
        """
        stmt = select(Sample).where(Sample.status == status).order_by(Sample.extraction_date)
        return list(self.session.scalars(stmt).all())

    def get_by_extraction_date_range(self, start: date, end: date) -> list[Sample]:
        """
        Returns all samples extracted within the given date range (inclusive).

        Example:
            from datetime import date
            samples = repo.get_by_extraction_date_range(date(2024, 1, 1), date(2024, 6, 30))
        """
        stmt = (
            select(Sample)
            .where(Sample.extraction_date >= start, Sample.extraction_date <= end)
            .order_by(Sample.extraction_date)
        )
        return list(self.session.scalars(stmt).all())

    # ── Lookup by related entity ──────────────────────────────────

    def get_by_patient_code(self, patient_code: str) -> list[Sample]:
        """
        Returns all samples belonging to a patient identified by their code.
        Performs a JOIN with the Patient table.

        Example:
            samples = repo.get_by_patient_code("P001")
            for sample in samples:
                print(sample.code, sample.status)
        """
        stmt = (
            select(Sample)
            .join(Patient, Patient.id == Sample.id_patient)
            .where(Patient.code == patient_code)
            .order_by(Sample.extraction_date)
        )
        return list(self.session.scalars(stmt).all())

    def get_by_container_code(self, container_code: str) -> list[Sample]:
        """
        Returns all samples stored in a container identified by its code.
        Performs a JOIN with the Container table.

        Example:
            samples = repo.get_by_container_code("CNT-003")
            for sample in samples:
                print(sample.code)
        """
        stmt = (
            select(Sample)
            .join(Container, Container.id == Sample.id_container)
            .where(Container.code == container_code)
        )
        return list(self.session.scalars(stmt).all())

    def get_by_sample_type(self, type_name: str) -> list[Sample]:
        """
        Returns all samples of a given type name.
        Performs a JOIN with the SampleType table.

        Example:
            blood_samples = repo.get_by_sample_type("Blood")
        """
        stmt = (
            select(Sample)
            .join(SampleType, SampleType.id == Sample.id_sample_type)
            .where(SampleType.type_name == type_name)
        )
        return list(self.session.scalars(stmt).all())

    # ── Eager loading ─────────────────────────────────────────────

    def get_with_protocols(self, code: str) -> Optional[Sample]:
        """
        Finds a sample AND eagerly loads its associated protocols.
        Useful when you need to access sample.protocols outside the session.

        Example:
            sample = repo.get_with_protocols("SMP-001")
            for protocol in sample.protocols:
                print(protocol.name)
        """
        stmt = (
            select(Sample)
            .where(Sample.code == code)
            .options(selectinload(Sample.protocols))
        )
        return self.session.scalar(stmt)

    def get_with_quality_control(self, code: str) -> Optional[Sample]:
        """
        Finds a sample AND eagerly loads its quality control record.
        Useful when you need to access sample.quality_control outside the session.

        Example:
            sample = repo.get_with_quality_control("SMP-001")
            if sample.quality_control:
                print(sample.quality_control.result)
        """
        stmt = (
            select(Sample)
            .where(Sample.code == code)
            .options(selectinload(Sample.quality_control))
        )
        return self.session.scalar(stmt)

    def get_with_log_temperatures(self, code: str) -> Optional[Sample]:
        """
        Finds a sample AND eagerly loads all its temperature log records.
        Useful when you need to access sample.log_temperatures outside the session.

        Example:
            sample = repo.get_with_log_temperatures("SMP-001")
            for log in sample.log_temperatures:
                print(log.reading_date, log.temperature)
        """
        stmt = (
            select(Sample)
            .where(Sample.code == code)
            .options(selectinload(Sample.log_temperatures))
        )
        return self.session.scalar(stmt)

    def get_full(self, code: str) -> Optional[Sample]:
        """
        Finds a sample AND eagerly loads ALL its related data in a single query:
        protocols, quality_control, log_temperatures, and research_projects.
        Use when you need a complete picture of a sample outside the session.

        Example:
            sample = repo.get_full("SMP-001")
            print(sample.quality_control.result)
            for protocol in sample.protocols:
                print(protocol.name)
        """
        stmt = (
            select(Sample)
            .where(Sample.code == code)
            .options(
                selectinload(Sample.protocols),
                selectinload(Sample.quality_control),
                selectinload(Sample.log_temperatures),
                selectinload(Sample.research_projects),
            )
        )
        return self.session.scalar(stmt)