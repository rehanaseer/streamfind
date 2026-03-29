"""
Shared test fixtures for StreamFind tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure src/ is importable
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import Base


@pytest.fixture
def db_session():
    """In-memory SQLite session with all tables created and defaults seeded."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    from src.repositories import seed_default_preferences
    seed_default_preferences(session)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
