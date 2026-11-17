from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.user import User
from schemas import recipe
from schemas.recipe import RecipeBase, RecipeCreate, RecipeResponse

# Retourne la liste de toutes les recettes.
def get_recipes(db: Session) -> list[Recipe]:
    return db.query(Recipe).all()


# Retourne les recettes appartenant à un utilisateur.
def get_recipes_by_owner(db: Session, owner_id: int) -> list[Recipe]:
    return db.query(Recipe).filter(Recipe.owner_id == owner_id).all()


def get_recipe(db: Session, recipe_id: int) -> Recipe | None:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()

# Recherche parmi les recettes des propriétaires donnés en combinant les filtres fournis (les filtres vides sont ignorés).
def search_recipes(db: Session, owner_ids: list[int], query: str = None, duration: int = None, servings: int = None) -> list[Recipe]:
    q = db.query(Recipe).filter(Recipe.owner_id.in_(owner_ids))
    if query:
        q = q.filter(Recipe.title.ilike(f"%{query}%"))
    # Durée maximale
    if duration is not None:
        q = q.filter(Recipe.duration <= duration)
    # Nombre de portions minimum
    if servings is not None:
        q = q.filter(Recipe.servings >= servings)
    return q.all()


def create_recipe(db: Session, recipe_data: RecipeCreate, owner_id: int) -> Recipe:
    recipe = Recipe(
        title=recipe_data.title,
        duration=recipe_data.duration,
        servings=recipe_data.servings,
        owner_id=owner_id,
    )

    db.add(recipe)
    db.commit()
    db.refresh(recipe)  # récupère l'id généré par la base
    return recipe


def update_recipe(db: Session, recipe: Recipe, recipe_data: RecipeBase) -> Recipe:
    recipe.title = recipe_data.title
    recipe.duration = recipe_data.duration
    recipe.servings = recipe_data.servings
    db.commit()
    db.refresh(recipe)
    return recipe

def delete_recipe(db: Session, recipe: Recipe) -> bool:
    db.delete(recipe)
    db.commit()
    return True

class RecipeNotFoundError(Exception):
    def __str__(self):
        return "Recette introuvable"


class UserNotFoundError(Exception):
    def __str__(self):
        return "L'Utilisateur n'existe pas"
