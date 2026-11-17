from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Route pour l'enregistrement d'un nouvel utilisateur
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = auth_service.get_user_by_username(db, user_data.username)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nom d'utilisateur déjà utilisé"
        )

    if auth_service.get_user_by_email(db, user_data.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email déjà utilisé"
        )

    user = auth_service.create_user(db, user_data)
    return user

# Route pour la connexion d'un utilisateur
@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.get_user_by_username(db, user_data.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )

    if not auth_service.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )

    token = auth_service.create_access_token(user.username)

    return {
        "access_token": token,
        "token_type": "bearer"
    }