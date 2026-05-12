from sqlalchemy import Table, Column, ForeignKey
from ..database import Base


# === PROTOCOLS PER SAMPLE (N:M) ===
# Since it only has foreign keys and no attributes, it should NOT be a class
# Python reads top to bottom, so the table must be defined before the classes use it

# Relationships ->
#   N:1 → Sample
#   N:1 → Protocol
sample_protocol = Table (
    "sample_protocol", Base.metadata,
    Column("id_protocol", ForeignKey("protocol.id", ondelete="CASCADE"), primary_key=True),
    Column("id_sample", ForeignKey("sample.id", ondelete="CASCADE"), primary_key=True)
)