import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, get_db
from backend.main import app

# Set environment to testing
os.environ["DB_ENV"] = "testing"

# Import base to ensure all models are registered
from backend.models import Account, Transaction, Transfer, Invoice, BankStatement

# Re-import database engine since DB_ENV changed
from backend.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create the test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    # We could drop tables here, but keeping it for inspection is often helpful
    # Base.metadata.drop_all(bind=engine)
    # Delete the test DB file after session
    if os.path.exists("./finance_tracker_test.db"):
        try:
            os.remove("./finance_tracker_test.db")
        except:
            pass

@pytest.fixture
def db_session():
    """Provides a fresh database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Provides a test client for the FastAPI application"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
