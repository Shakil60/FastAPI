"""Données initiales : un utilisateur de démo et quelques recettes.

À lancer une seule fois après la première migration :
    en local    : python seed.py
    sur Scalingo: scalingo --app <app-api> run python seed.py
Le script ne fait rien si l'utilisateur de démo existe déjà.
"""
import os

from database import SessionLocal
from models.recipe import Recipe
from models.user import User
from services.auth_service import hash_password

DEMO_USERNAME = os.getenv("SEED_USERNAME", "demo")
DEMO_EMAIL = os.getenv("SEED_EMAIL", "demo@example.com")
DEMO_PASSWORD = os.getenv("SEED_PASSWORD", "demo1234")

INITIAL_RECIPES = [
    {"title": "Quiche lorraine", "duration": 60, "servings": 6},
    {"title": "Boeuf bourguignon", "duration": 180, "servings": 6},
    {"title": "Ratatouille", "duration": 75, "servings": 4},
    {"title": "Crêpes sucrées", "duration": 30, "servings": 4},
    {"title": "Gratin dauphinois", "duration": 90, "servings": 6},
]


def main():
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == DEMO_USERNAME).first():
            print(f"Utilisateur '{DEMO_USERNAME}' déjà présent, rien à faire.")
            return
        user = User(username=DEMO_USERNAME, email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()  # récupère user.id
        db.add_all(Recipe(owner_id=user.id, **data) for data in INITIAL_RECIPES)
        db.commit()
        print(f"Utilisateur '{DEMO_USERNAME}' et {len(INITIAL_RECIPES)} recettes créés.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
