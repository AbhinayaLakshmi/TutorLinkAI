import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.session import get_db
from backend.app.models.base import Base
from backend.app.core.config import settings

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Override get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    """
    Automatically mocks the email sender service for all tests.
    Saves the generated plain OTP in the settings cache for verification.
    """
    def mock_send_otp_email(to_email: str, otp: str) -> None:
        settings.TEST_OTP_STORE[to_email] = otp
        
    # Patch in both the services definition and the imported route reference
    monkeypatch.setattr("backend.app.services.email.send_otp_email", mock_send_otp_email)
    monkeypatch.setattr("backend.app.modules.onboarding.routes.send_otp_email", mock_send_otp_email)
