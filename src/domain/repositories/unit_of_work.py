from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class AbstractUnitOfWork(ABC):
    """
    El 'Unit of Work' (UoW) se encarga de gestionar una transacción completa.
    Imaginalo como un sobre: pones todas tus operaciones dentro y, al final,
    o se envían todas juntas o se rompe el sobre y no se envía nada.
    """

    def __enter__(self):
        """Inicia el contexto de trabajo (ej. 'with uow:')"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Se ejecuta automáticamente al salir del bloque 'with'.
        Si hubo un error (exc_type no es None), hace rollback.
        Si todo fue bien, hace commit.
        """
        if exc_type:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self) -> None:
        """Confirma todos los cambios realizados en esta unidad de trabajo."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Cancela todos los cambios si algo salió mal."""
        pass

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Implementación específica de UoW para SQLAlchemy.
    Maneja la sesión real de la base de datos.
    """

    def __init__(self, session: Session):
        self.session = session

    def __exit__(self, exc_type, exc_value, traceback):
        # Primero llamamos al comportamiento base (decidir si commit o rollback)
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            # Muy importante: Siempre cerramos la sesión para liberar recursos
            # pase lo que pase (error o éxito).
            self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

class UnitOfWorkFactory:
    """
    La Fabrica es el punto de entrada para nuestra aplicación.
    Configura la conexión una sola vez y nos da 'Unidades de Trabajo' listas para usar.
    """

    def __init__(self, database_url: str):
        # El motor (engine) es el puente hacia la base de datos (ej. SQLite).
        self.engine = create_engine(database_url)
        # sessionmaker crea una 'clase' de sesión configurada con nuestras reglas.
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def create(self) -> SqlAlchemyUnitOfWork:
        """Crea una nueva sesión y la envuelve en un Unit of Work."""
        return SqlAlchemyUnitOfWork(self.session_factory())