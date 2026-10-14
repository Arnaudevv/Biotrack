from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Container
from .base_repository import BaseRepository


class ContainerRepository(BaseRepository[Container, int]):
    """Repository for container persistence and container-specific lookups."""

    def __init__(self, session: Session):
        super().__init__(session, Container)

    def get_by_code_or_type_name(
        self, code: str, type_name: str
    ) -> Optional[Container]:
        """Finds a container conflicting with either unique field."""
        stmt = select(Container).where(
            (Container.code == code) | (Container.type_name == type_name)
        )
        return self.session.scalar(stmt)
