import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.database.models import Base, User, SMTPConf

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_create_user(setup_database):
    session = setup_database
    user = User(username="testuser", email="test@example.com", password="password123")
    session.add(user)
    session.commit()
    queried = session.query(User).filter_by(username="testuser").first()
    assert queried is not None
    assert queried.email == "test@example.com"

def test_create_smtpconf(setup_database):
    session = setup_database
    user = User(username="smtpuser", email="smtp@example.com", password="smtp123")
    session.add(user)
    session.commit()
    smtp = SMTPConf(smtp_host="smtp.test.com", smtp_port=587, smtp_username="smtp@example.com", smtp_password="smtp_pass", sender_email="smtp@example.com")
    session.add(smtp)
    session.commit()
    queried = session.query(SMTPConf).filter_by(smtp_username="smtp@example.com").first()
    assert queried is not None
    assert queried.smtp_host == "smtp.test.com"
    assert queried.user.email == "smtp@example.com"
