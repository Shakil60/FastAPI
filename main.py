import time
from datetime import datetime

from fastapi import  FastAPI, Request

import models.recipe as recipe
import models.user as user

from database import Base, SessionLocal, engine

from routes.recipe import INITIAL_RECIPES
from routes.recipe import router as recipe_router
from routes.auth import router as auth_router
from routes.user import router as user_router

Base.metadata.create_all(bind=engine)

# Insère les recettes initiales uniquement si la table est vide
db = SessionLocal()
if db.query(recipe.Recipe).count() == 0:
    db.bulk_insert_mappings(recipe.Recipe, INITIAL_RECIPES)
    db.commit()
db.close()

app = FastAPI(title="firstAPI", version="1.0.0")

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