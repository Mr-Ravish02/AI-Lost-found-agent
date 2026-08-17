import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.item import LostItem, FoundItem, Match, VerificationQuestion, VerificationAnswer
from app.utils.security import create_access_token, get_password_hash

# In-memory test SQLite DB with StaticPool for multi-threaded TestClient sharing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def claimant_user(db):
    user = User(
        email="claimant@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Claimant Alice",
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": user.email})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture(scope="function")
def finder_user(db):
    user = User(
        email="finder@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Finder Bob",
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": user.email})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture(scope="function")
def admin_user(db):
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin Chief",
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": user.email})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture(scope="function")
def stranger_user(db):
    user = User(
        email="stranger@example.com",
        hashed_password=get_password_hash("strangerpass123"),
        full_name="Stranger Dave",
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": user.email})
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture(scope="function")
def sample_match(db, claimant_user, finder_user):
    lost = LostItem(
        user_id=claimant_user["user"].id,
        title="Black Dell XPS 15 Laptop",
        category="Electronics",
        description="Black Dell XPS laptop lost near library 2nd floor study room. Has a red sticker on the back lid.",
        color="Black",
        brand="Dell",
        model="XPS 15",
        location="Library 2nd floor",
        date_lost="2026-03-01",
        distinctive_features=["red sticker on back lid", "scratch near trackpad"],
        status="active"
    )
    db.add(lost)
    db.commit()
    db.refresh(lost)

    # Found item contains private secret detail NOT in lost report: "Secret USB drive in side pocket"
    found = FoundItem(
        user_id=finder_user["user"].id,
        title="Found Dell Laptop in Library",
        category="Electronics",
        description="Black Dell laptop found on library table. Red sticker on lid and a secret blue SanDisk 64GB USB drive inside the sleeve pocket.",
        color="Black",
        brand="Dell",
        model="XPS",
        location="Main Library",
        date_found="2026-03-01",
        distinctive_features=["red sticker", "blue SanDisk USB drive in secret sleeve"],
        status="active"
    )
    db.add(found)
    db.commit()
    db.refresh(found)

    match = Match(
        lost_item_id=lost.id,
        found_item_id=found.id,
        match_score=92.5,
        confidence_level="high",
        factor_breakdown={"category": 100, "brand": 100, "color": 100, "text": 85},
        reasons=["Category match: Electronics", "Brand match: Dell", "Color match: Black"],
        status="pending"
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    return {"lost": lost, "found": found, "match": match}
