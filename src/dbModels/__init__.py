from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from src.dbModels.SchemaModels import (
    User, College, Event, Sponsorship, Achievement, Match,
    GameCategory, Participant, Team, Schedule, Venue, Certificate
)
from src.dbModels.BaseModel import Base
from src.utils.pre_loader import config
from .models import *

# Corrected SQLite URL for a relative path
_engine = create_engine(
    environ.get("SQLALCHEMY_DATABASE_URI"),
    echo=(config.getboolean("database", "echo")),
    poolclass=QueuePool,  # Use QueuePool for connection pooling
    pool_size=config.getint("database", "pool_size", fallback=5),
    max_overflow=config.getint("database", "max_overflow", fallback=10),
    pool_timeout=config.getint("database", "pool_timeout", fallback=30),
)

# Create tables
Base.metadata.create_all(_engine)

dbSession = sessionmaker(bind=_engine)
