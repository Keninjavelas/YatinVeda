"""
Pytest configuration and shared fixtures for backend tests
"""

import os

# CRITICAL: Set environment flags to disable rate limiting BEFORE any other imports
# This ensures that when auth.py and profile.py are imported (transitively through main.py),
# the rate_limit decorator factories will evaluate these variables and return no-op decorators.
os.environ["DISABLE_RATELIMIT"] = "1"
os.environ["PYTEST_CURRENT_TEST"] = "conftest.py::setup"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import get_db
from models.database import Base, User, Chart
from modules.auth import get_password_hash, create_access_token

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("TestPass123"),  # Now meets complexity requirements (8+ chars, uppercase, lowercase, digit)
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user):
    """Generate JWT token for test user with user_id (matches login endpoint)"""
    return create_access_token(data={"sub": test_user.username, "user_id": test_user.id})


@pytest.fixture
def auth_headers(test_user_token):
    """Create authorization headers with JWT token"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def second_test_user(db_session):
    """Create a second test user for ownership tests"""
    user = User(
        username="seconduser",
        email="second@example.com",
        password_hash=get_password_hash("SecondPass456"),  # Meets complexity requirements
        full_name="Second User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_token(second_test_user):
    """Generate JWT token for second test user"""
    return create_access_token(data={"sub": second_test_user.username, "user_id": second_test_user.id})


@pytest.fixture
def second_auth_headers(second_user_token):
    """Create authorization headers for second test user"""
    return {"Authorization": f"Bearer {second_user_token}"}


@pytest.fixture
def sample_chart_data():
    """Sample chart data for testing"""
    return {
        "chart_name": "Test Birth Chart",
        "birth_details": {
            "date": "1990-01-15",
            "time": "14:30:00",
            "location": "New Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090
        },
        "chart_data": {
            "ascendant": "Aries",
            "houses": [
                {"house": 1, "sign": "Aries", "planets": ["Sun", "Mars"]},
                {"house": 2, "sign": "Taurus", "planets": []},
                # ... other houses
            ]
        },
        "chart_type": "D1",
        "is_public": False
    }


@pytest.fixture
def create_test_chart(db_session, test_user, sample_chart_data):
    """Factory fixture to create test charts"""
    def _create_chart(**kwargs):
        chart_data = sample_chart_data.copy()
        chart_data.update(kwargs)
        
        chart = Chart(
            user_id=test_user.id,
            chart_name=chart_data["chart_name"],
            birth_details=chart_data["birth_details"],
            chart_data=chart_data["chart_data"],
            chart_type=chart_data.get("chart_type", "D1"),
            is_public=chart_data.get("is_public", False)
        )
        db_session.add(chart)
        db_session.commit()
        db_session.refresh(chart)
        return chart
    
    return _create_chart
