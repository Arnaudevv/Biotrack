# =============================================================================
# DATABASE ENGINE & SESSION CONFIGURATION
# =============================================================================
# This module initializes the SQLAlchemy engine and session factory.
# It acts as the primary bridge between the Python application and the 
# physical database, managing connection pooling and ORM mapping.
#
# COMPONENTS:
# - Engine: Manages the low-level connection to the database.
# - Base: The declarative base class for all domain models.
# - Session: A configured factory for generating database sessions.
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import DB_URL

# The engine handles the physical connection to the DB.
# It uses the URL provided in the configuration (e.g., PostgreSQL, SQLite).
# Setting echo=True would log all generated SQL queries to the console.
engine = create_engine(DB_URL)

# DeclarativeBase is the parent class for all ORM models.
# It serves as a registry, allowing SQLAlchemy to track all defined tables.
# All domain models must inherit from this class.
class Base(DeclarativeBase):
    pass

# Session is a factory (template) for database transactions.
# Each time a database operation is required, an instance should be created.
# Usage: with Session() as session: ...
Session = sessionmaker(bind=engine)