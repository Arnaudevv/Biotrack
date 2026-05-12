# Structure:
#   BaseRepository[T]             → common CRUD operations for ALL tables
#   ├── PatientRepository         → Patient-specific queries
#   ├── StaffRepository           → Staff-specific queries
#   ├── ResearchProjectRepository → ResearchProject-specific queries
#   ├── SampleRepository          → Sample-specific queries        (pending)
#   └── ProtocolRepository        → Protocol-specific queries      (pending)
# ─────────────────────────────────────────────────────────────────

from .base_repository import BaseRepository
from .patient_repository import PatientRepository
from .staff_repository import StaffRepository
from .research_project_repository import ResearchProjectRepository

__all__ = [
    "BaseRepository",
    "PatientRepository",
    "StaffRepository",
    "ResearchProjectRepository",
]