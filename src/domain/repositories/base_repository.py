# Python standard library
from typing import Generic, TypeVar, Optional

# SQLAlchemy
from sqlalchemy.orm import Session
from sqlalchemy import select

# T represents any model class (Patient, Staff, Sample...)
# It's a "type wildcard" that tells Python:
# "this repository works with any model, not just one specific one"
T = TypeVar("T")    # Entity type (Patient, Staff, ...)
ID = TypeVar("ID")  # ID type (int, str, ...)


# ══════════════════════════════════════════════════════════════════
# BASE REPOSITORY
# CRUD operations that work the same for ANY table.
# All specific repositories inherit from here.
# ══════════════════════════════════════════════════════════════════

class BaseRepository(Generic[T]):
    """
    Base repository with operations common to all tables.

    Receives two things on creation:
        - session: the active SQLAlchemy session (the "conversation" with the DB)
        - model:   the model class it works with (Patient, Staff...)

    Usage:
        with Session() as session:
            repo = PatientRepository(session)
    """

    def __init__(self, session: Session, model: type[T]):
        self.session = session
        self.model = model

    # ── Read ──────────────────────────────────────────────────────

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Finds a record by its primary key (id).

        Returns the object if found  -  Returns None if not found

        Example  ->  patient = repo.get_by_id(3)
        """
        return self.session.get(self.model, id)

    def get_all(self) -> list[T]:
        """
        Returns all records in the table.

        Example:
            patients = repo.get_all()
        """
        return self.session.scalars(select(self.model)).all()

    # ── Write ─────────────────────────────────────────────────────

    def save(self, entity: T) -> T:
        """
        Saves a new object or updates an existing one.

        Example:
            patient = Patient(code="P010", name="Ana", ...)
            patient = repo.save(patient)
            print(patient.id)  # already has the DB-assigned id
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """
        Deletes a record from the DB.

        Example:
            patient = repo.get_by_id(3)
            repo.delete(patient)
        """
        self.session.delete(entity)
        self.session.commit()

    def count(self) -> int:
        """
        Counts how many records exist in the table.

        Example:
            total = repo.count()
            print(f"There are {total} patients")
        """
        return self.session.scalars(select(self.model)).all().__len__()