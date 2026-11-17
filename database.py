from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base SQLite stockée dans le fichier recipe.db à la racine du projet
DATABASE_URL = f"sqlite:///./recipe.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# Dépendance FastAPI : ouvre une session pour la requête et la ferme à la fin.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()