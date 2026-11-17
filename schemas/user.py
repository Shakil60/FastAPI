from pydantic import BaseModel, EmailStr, Field

#Structure de données pour un utilisateur
class UserBase(BaseModel):
    username: str
    password: str


# Validation à l'inscription : username de 3 à 30 caractères, email valide, mot de passe de 8 caractères minimum
class UserCreate(UserBase):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)


# La connexion ne demande que le nom d'utilisateur et le mot de passe
class UserLogin(UserBase):
    pass


class UserResponse(BaseModel):
    username: str
    email: str
    id: int
    class Config:
        from_attributes = True

#Structure de données pour le token d'authentification
class Token(BaseModel):
    access_token: str
    token_type: str


# Partage de ses recettes avec un autre utilisateur (lecture seule par défaut)
class AccessCreate(BaseModel):
    username: str
    can_edit: bool = False


class AccessResponse(BaseModel):
    owner_id: int
    grantee_id: int
    can_edit: bool

    class Config:
        from_attributes = True
