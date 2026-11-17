from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
from database import get_db

from routes.recipe import router as recipe_router
from routes.auth import router as auth_router
from routes.user import router as user_router

# Le schéma de la base est géré par Alembic (alembic upgrade head), plus de create_all au démarrage
app = FastAPI(title="firstAPI", version="1.0.0")

# Autorise le client (origines listées dans CORS_ORIGINS) à appeler l'API depuis le navigateur
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes des recettes
app.include_router(recipe_router)

# Enregistrement des routes d'authentification
app.include_router(auth_router)

# Enregistrement des routes utilisateur
app.include_router(user_router)

# Vérifie que l'API est bien lancée
@app.get("/")
def root():
    return {"message": "Recipe API is running"}

# Vérifie que l'API et la base de données répondent (200 si tout va bien, 503 sinon)
@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Base de données injoignable")
    return {"status": "ok"}
