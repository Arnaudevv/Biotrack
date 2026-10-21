# Python standard library
from typing import Optional

# SQLAlchemy
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

# Internal - models
from ..models import Protocol, Staff

# Internal - repositories
from .base_repository import BaseRepository


# ══════════════════════════════════════════════════════════════════
# PROTOCOL REPOSITORY
# ══════════════════════════════════════════════════════════════════

class ProtocolRepository(BaseRepository[Protocol, int]):
    """
    Repository for the Protocol table.
    Inherits get_by_id, get_all, save, delete and count from BaseRepository.
    Adds Protocol-specific methods.
    """

    def __init__(self, session: Session):
        super().__init__(session, Protocol)

    # ── Lookup by field ───────────────────────────────────────────

    def get_by_code(self, code: str) -> Optional[Protocol]:
        """
        Finds a protocol by its unique code (e.g. "PROT-001").
        Returns None if not found.

        Example:
            protocol = repo.get_by_code("PROT-001")
        """
        stmt = select(Protocol).where(Protocol.code == code)
        return self.session.scalar(stmt)

    def search_by_name(self, keyword: str) -> list[Protocol]:
        """
        Returns all protocols whose name contains the given keyword (case-insensitive).
        Useful for autocomplete or search forms.

        Example:
            results = repo.search_by_name("extraction")
            for protocol in results:
                print(protocol.code, protocol.name)
        """
        stmt = select(Protocol).where(Protocol.name.ilike(f"%{keyword}%"))
        return list(self.session.scalars(stmt).all())

    def get_unreviewed(self) -> list[Protocol]:
        """
        Returns all protocols that have not been reviewed yet
        (i.e. reviewed_by_id is NULL).

        Example:
            pending = repo.get_unreviewed()
            print(f"{len(pending)} protocols still need review")
        """
        stmt = select(Protocol).where(Protocol.reviewed_by_id == None)
        return list(self.session.scalars(stmt).all())

    # ── Lookup by related entity ──────────────────────────────────

    def get_by_reviewer(self, staff_code: str) -> list[Protocol]:
        """
        Returns all protocols reviewed by the staff member identified by their code.
        Performs a JOIN with the Staff table.

        Example:
            protocols = repo.get_by_reviewer("S001")
            for protocol in protocols:
                print(protocol.code, protocol.name)
        """
        stmt = (
            select(Protocol)
            .join(Staff, Staff.id == Protocol.reviewed_by_id)
            .where(Staff.code == staff_code)
        )
        return list(self.session.scalars(stmt).all())

    # ── Eager loading ─────────────────────────────────────────────

    def get_with_samples(self, code: str) -> Optional[Protocol]:
        """
        Finds a protocol AND eagerly loads all samples it has been applied to.
        Useful when you need to access protocol.samples outside the session.

        Example:
            protocol = repo.get_with_samples("PROT-001")
            for sample in protocol.samples:
                print(sample.code)
        """
        stmt = (
            select(Protocol)
            .where(Protocol.code == code)
            .options(selectinload(Protocol.samples))
        )
        return self.session.scalar(stmt)