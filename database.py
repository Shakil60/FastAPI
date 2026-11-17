from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

# pool_pre_ping évite les erreurs sur des connexions fermées par le serveur PostgreSQL
engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# Dépendance FastAPI : ouvre une session pour la requête et la ferme à la fin.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
