from pwdlib import PasswordHash

from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from database import get_db

from schemas.user import UserCreate

# Algorithme de hachage recommandé par pwdlib (Argon2)
password_hash = PasswordHash.recommended()

# Récupère le token envoyé dans le header "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()

# Paramètres JWT
SECRET_KEY = "test_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# Crée un utilisateur en base avec son mot de passe haché.
def create_user(db, user: UserCreate):
    from models.user import User
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # récupère l'id généré par la base
    return new_user

def get_user_by_username(db, username: str):
    from models.user import User
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db, email: str):
    from models.user import User
    return db.query(User).filter(User.email == email).first()

# Génère un token JWT signé contenant le nom d'utilisateur et une date d'expiration.
def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username, 
        "exp": expire,    
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token

def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Vérifie la signature et la date d'expiration (exp)
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception

    # Le token doit contenir le nom d'utilisateur dans "sub"
    username = payload.get("sub")
    if username is None:
        raise credentials_exception

    return username

# Retourne l'utilisateur connecté à partir du token (401 s'il n'existe plus en base).
def get_current_user(username: str = Depends(get_current_username), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
