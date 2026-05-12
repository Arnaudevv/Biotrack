# Information / Notes
# > __tablename__ = "table"
# If the table already exists in the DB -> SQLAlchemy maps it (connects it to the class)
# If the table does NOT exist in the DB -> SQLAlchemy creates it when create_all() is called

# id: Mapped[int] = mapped_column(Integer, primary_key=True)
# id              -> column name (same as in SQL)
# Mapped[int]     -> tells Python "this will be an integer"
# mapped_column() -> defines how the column is structured in the DB
# Integer         -> data type in the DB
# primary_key=True -> sets it as the primary key

# Auto-increment -> If a column is Integer and a primary key, SQLAlchemy makes it implicitly auto-incrementing
# To disable auto-increment -> autoincrement=False

# // =========== MODELS =========== //
# Importing all models here ensures that SQLAlchemy registers them in the metadata
# before calling create_all(), and also allows them to be imported directly from the package:
# from models import Patient, Sample,..

from .association_tables import sample_protocol
from .patient import Patient
from .staff import Staff
from .sample_type import SampleType
from .container import Container
from .research_project import ResearchProject
from .sample import Sample
from .protocol import Protocol
from .log_temperature import LogTemperature
from .quality_control import QualityControl
from .research_project_samples import ResearchProjectSamples
from .project_team import ProjectTeam
 
__all__ = [
    "sample_protocol",
    "Patient",
    "Staff",
    "SampleType",
    "Container",
    "ResearchProject",
    "Sample",
    "Protocol",
    "LogTemperature",
    "QualityControl",
    "ResearchProjectSamples",
    "ProjectTeam",
]