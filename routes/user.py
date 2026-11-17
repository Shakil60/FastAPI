from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.recipe import RecipeResponse
from schemas.user import AccessCreate, AccessResponse, UserResponse
from services import auth_service, recipe_service, user_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

# Route pour récupérer les informations de l'utilisateur connecté (sans le mot de passe)
@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

# Route pour lister les recettes appartenant à l'utilisateur connecté
@router.get("/me/recipes", response_model=list[RecipeResponse])
def read_my_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return recipe_service.get_recipes_by_owner(db, current_user.id)

# Route pour lister les accès accordés par l'utilisateur connecté
@router.get("/me/accesses", response_model=list[AccessResponse])
def read_my_accesses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return user_service.get_granted_accesses(db, current_user)

# Route pour lister les accès reçus par l'utilisateur connecté
@router.get("/me/accesses/received", response_model=list[AccessResponse])
def read_received_accesses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return user_service.get_received_accesses(db, current_user)

# Route pour partager ses recettes avec un autre utilisateur (met à jour le droit si l'accès existe déjà)
@router.post("/me/accesses", response_model=AccessResponse, status_code=status.HTTP_201_CREATED)
def grant_access(access_data: AccessCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    grantee = auth_service.get_user_by_username(db, access_data.username)
    if grantee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="L'Utilisateur n'existe pas")
    if grantee.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas vous accorder un accès")
    return user_service.grant_access(db, current_user, grantee, access_data.can_edit)

# Route pour retirer l'accès accordé à un utilisateur
@router.delete("/me/accesses/{grantee_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_access(grantee_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    access = user_service.get_access(db, current_user.id, grantee_id)
    if access is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accès introuvable")
    user_service.revoke_access(db, access)
    return None
