import os

# Valeurs par défaut pour les tests (la CI fournit DATABASE_URL vers un PostgreSQL de service)
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app
import models.recipe  # noqa: F401  (enregistre les tables dans Base.metadata)
import models.user  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def schema():
    # En CI le schéma est déjà créé par "alembic upgrade head" : create_all ne fait alors rien
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    # Chaque test part d'une base vide
    db = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register_and_login(client, username, password="password123"):
    client.post("/auth/register", json={
        "username": username, "email": f"{username}@example.com", "password": password,
    })
    token = client.post("/auth/login", json={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
