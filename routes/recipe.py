from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.recipe import Recipe
from models.user import User
from schemas.recipe import RecipeCreate, RecipeResponse
from services import recipe_service, user_service
from services.auth_service import get_current_user

INITIAL_RECIPES = [
    {"id": 1, "title": "Quiche lorraine", "duration": 60, "servings": 6, "owner_id": 1},
    {"id": 2, "title": "Boeuf bourguignon", "duration": 180, "servings": 6, "owner_id": 1},
    {"id": 3, "title": "Ratatouille", "duration": 75, "servings": 4, "owner_id": 1},
    {"id": 4, "title": "Crêpes sucrées", "duration": 30, "servings": 4, "owner_id": 1},
    {"id": 5, "title": "Gratin dauphinois", "duration": 90, "servings": 6, "owner_id": 1},
]

router = APIRouter(prefix="/recipes", tags=["Recipes"])

# Récupère une recette (404 si absente)
def get_recipe_or_404(recipe_id: int, db: Session) -> Recipe:
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recette introuvable")
    return recipe

# Route pour lister les recettes accessibles (les siennes et celles partagées avec soi) avec filtres optionnels
@router.get("", response_model=list[RecipeResponse])
def get_recipes(db: Session = Depends(get_db), query: str = None, duration: int = None, servings: int = None,
                current_user: User = Depends(get_current_user)):
    owner_ids = user_service.get_readable_owner_ids(db, current_user)
    return recipe_service.search_recipes(db, owner_ids, query, duration, servings)


# Route pour récupérer les détails d'une recette (propriétaire ou utilisateur ayant un accès)
@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recipe = get_recipe_or_404(recipe_id, db)
    if not user_service.can_read(db, current_user, recipe):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'avez pas accès à cette recette")
    return recipe

# Route pour créer une recette (accessible uniquement aux utilisateurs authentifiés)
@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return recipe_service.create_recipe(db, recipe, current_user.id)

# Route pour mettre à jour une recette (propriétaire ou utilisateur ayant un accès en modification)
@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, recipe: RecipeCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    existing_recipe = get_recipe_or_404(recipe_id, db)
    if not user_service.can_edit(db, current_user, existing_recipe):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez pas modifier cette recette")
    return recipe_service.update_recipe(db, existing_recipe, recipe)

# Route pour supprimer une recette (uniquement par son propriétaire)
@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    recipe = get_recipe_or_404(recipe_id, db)
    if not user_service.can_delete(current_user, recipe):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le propriétaire peut supprimer cette recette")
    recipe_service.delete_recipe(db, recipe)
    return None
