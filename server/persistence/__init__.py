# This file turns the domain/ folder into a Python package.
# It allows imports like: from domain import Base, engine...
# It also defines what is exposed when importing from domain.

from .config import ENVIRONMENT, DB_URL
from .database import Base, engine, Session
from .models import (
    Patient, Staff, SampleType, Container,
    ResearchProject, Sample, Protocol,
    LogTemperature, QualityControl,
    ResearchProjectSamples, ProjectTeam
)
from .repositories import (
    BaseRepository, PatientRepository, ResearchProjectRepository, StaffRepository
)