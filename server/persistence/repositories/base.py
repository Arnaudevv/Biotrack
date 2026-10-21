from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Sequence, Type
from sqlalchemy.orm import Session

# Generic type definitions for domain entities and their primary key identifiers.
T = TypeVar("T")
ID = TypeVar("ID")

class AbstractRepository(ABC, Generic[T, ID]):
    """
    Interface for the Repository pattern.
    Defines the required data access operations for any concrete repository implementation.
    """

    @abstractmethod
    def add(self, entity: T) -> None:
        """Persists a new entity instance."""
        pass

    @abstractmethod
    def update(self, entity: T) -> None:
        """Updates an existing entity instance."""
        pass

    @abstractmethod
    def get(self, entity_id: ID) -> Optional[T]:
        """Retrieves an entity by its unique primary identifier."""
        pass

    @abstractmethod
    def list(self) -> Sequence[T]:
        """Retrieves all instances of the current entity type."""
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        """Removes an entity instance from the system."""
        pass

class SqlAlchemyRepository(AbstractRepository[T, ID]):
    """
    SQLAlchemy-specific implementation of the Repository pattern.
    Handles the translation between domain operations and database commands.
    """

    def __init__(self, session: Session, model_class: Type[T]):
        # Dependency injection of the session, typically managed by a Unit of Work.
        # This ensures all repositories within a transaction scope share the same session.
        self.session = session
        self.model_class = model_class

    def add(self, entity: T) -> None:
        self.session.add(entity)

    def get(self, entity_id: ID) -> Optional[T]:
        # Utilizes the session's optimized identity map lookup.
        return self.session.get(self.model_class, entity_id)

    def update(self, entity: T) -> None:
        # No explicit operation is required as SQLAlchemy's unit of work 
        # pattern automatically tracks changes to objects within the session.
        pass

    def list(self) -> Sequence[T]:
        return self.session.query(self.model_class).all()

    def delete(self, entity: T) -> None:
        self.session.delete(entity)