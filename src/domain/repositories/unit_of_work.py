from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class AbstractUnitOfWork(ABC):
    """
    Interface for the Unit of Work pattern.
    Ensures atomicity by managing the transaction lifecycle across multiple repositories.
    """

    def __enter__(self):
        """Initializes the context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Finalizes the transaction context.
        Performs a rollback if an exception occurred; otherwise, commits the changes.
        """
        if exc_type:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self) -> None:
        """Persists all changes made within the current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Reverts all changes made during the current transaction."""
        pass

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy-specific implementation of the Unit of Work.
    Manages the lifecycle of a SQLAlchemy Session.
    """

    def __init__(self, session: Session):
        self.session = session

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            # Ensure the session is closed to release connection pool resources,
            # regardless of whether the transaction succeeded or failed.
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

class UnitOfWorkFactory:
    """
    Factory responsible for database engine initialization and session configuration.
    Acts as the main entry point for creating Unit of Work instances.
    """

    def __init__(self, database_url: str):
        # Initialize the database engine with the provided connection string.
        self.engine = create_engine(database_url)
        
        # Configure the session factory with standard defaults for the UoW pattern.
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def create(self) -> SqlAlchemyUnitOfWork:
        """Instantiates a new SQLAlchemy session and wraps it in a Unit of Work."""
        return SqlAlchemyUnitOfWork(self.session_factory())