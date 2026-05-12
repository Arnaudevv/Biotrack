# Python standard library
from typing import Optional
from datetime import datetime

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy import select

# Internal - models
from ..models import LogTemperature, Sample

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# LOG TEMPERATURE REPOSITORY
# ══════════════════════════════════════════════════════════════════

class LogTemperatureRepository(BaseRepository[LogTemperature, int]):
    """
    Repository for the LogTemperature table.
    Inherits get_by_id, get_all, save, delete and count from BaseRepository.
    Adds LogTemperature-specific methods.
    """

    def __init__(self, session: Session):
        super().__init__(session, LogTemperature)

    # ── Lookup by related entity ──────────────────────────────────

    def get_by_sample_code(self, sample_code: str) -> list[LogTemperature]:
        """
        Returns all temperature records associated with the given sample code,
        ordered from oldest to most recent reading.
        Performs a JOIN with the Sample table.

        Example:
            logs = repo.get_by_sample_code("SMP-001")
            for log in logs:
                print(log.reading_date, log.temperature)
        """
        stmt = (
            select(LogTemperature)
            .join(Sample, Sample.id == LogTemperature.id_sample)
            .where(Sample.code == sample_code)
            .order_by(LogTemperature.reading_date)
        )
        return list(self.session.scalars(stmt).all())

    def get_latest_by_sample_code(self, sample_code: str) -> Optional[LogTemperature]:
        """
        Returns the most recent temperature record for the given sample code.
        Returns None if no records exist for that sample.

        Example:
            latest = repo.get_latest_by_sample_code("SMP-001")
            if latest:
                print(f"Last reading: {latest.temperature}°C at {latest.reading_date}")
        """
        stmt = (
            select(LogTemperature)
            .join(Sample, Sample.id == LogTemperature.id_sample)
            .where(Sample.code == sample_code)
            .order_by(LogTemperature.reading_date.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_by_date_range(
        self, sample_code: str, start: datetime, end: datetime
    ) -> list[LogTemperature]:
        """
        Returns all temperature records for a sample within the given datetime range
        (inclusive), ordered chronologically.

        Example:
            from datetime import datetime
            logs = repo.get_by_date_range(
                "SMP-001",
                datetime(2024, 6, 1),
                datetime(2024, 6, 30, 23, 59, 59)
            )
        """
        stmt = (
            select(LogTemperature)
            .join(Sample, Sample.id == LogTemperature.id_sample)
            .where(
                Sample.code == sample_code,
                LogTemperature.reading_date >= start,
                LogTemperature.reading_date <= end,
            )
            .order_by(LogTemperature.reading_date)
        )
        return list(self.session.scalars(stmt).all())

    def get_out_of_range(
        self, min_temp: float, max_temp: float
    ) -> list[LogTemperature]:
        """
        Returns all temperature records where the reading falls outside
        the acceptable range [min_temp, max_temp]. Useful for flagging anomalies.

        Example:
            anomalies = repo.get_out_of_range(min_temp=-80.0, max_temp=-60.0)
            for log in anomalies:
                print(f"Sample {log.id_sample}: {log.temperature}°C on {log.reading_date}")
        """
        stmt = select(LogTemperature).where(
            (LogTemperature.temperature < min_temp)
            | (LogTemperature.temperature > max_temp)
        )
        return list(self.session.scalars(stmt).all())