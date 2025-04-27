import pytest
from sqlalchemy import create_engine, text
from src.config import get_database_url

@pytest.fixture(scope="session")
def database_engine():
    """fixture for database engine"""
    engine = create_engine(get_database_url())
    try:
        # connection test
        with engine.connect():
            yield engine
    except Exception as e:
        pytest.skip(f"!!!!!!!  Connection Error !!!!!!!!!: {str(e)}")

def test_database_connection(database_engine):
    """DB connection test"""
    with database_engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        
    assert result == 1, "!!!!!!!!  Failed to connect to the database !!!!!!!!!"