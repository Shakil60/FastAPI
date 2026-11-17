from sqlalchemy.orm import Session

from models.recipe import Recipe
from models.user import Access, User


# Retourne l'accès accordé par un propriétaire à un utilisateur (None si aucun).
def get_access(db: Session, owner_id: int, grantee_id: int) -> Access | None:
    return db.query(Access).filter(Access.owner_id == owner_id, Access.grantee_id == grantee_id).first()


# Retourne les ids des propriétaires dont l'utilisateur peut lire les recettes (lui-même inclus).
def get_readable_owner_ids(db: Session, user: User) -> list[int]:
    shared = db.query(Access.owner_id).filter(Access.grantee_id == user.id).all()
    return [user.id] + [owner_id for (owner_id,) in shared]


def can_read(db: Session, user: User, recipe: Recipe) -> bool:
    return recipe.owner_id == user.id or get_access(db, recipe.owner_id, user.id) is not None


def can_edit(db: Session, user: User, recipe: Recipe) -> bool:
    if recipe.owner_id == user.id:
        return True
    access = get_access(db, recipe.owner_id, user.id)
    return access is not None and access.can_edit


# Seul le propriétaire peut supprimer sa recette
def can_delete(user: User, recipe: Recipe) -> bool:
    return recipe.owner_id == user.id


# Retourne les accès accordés par l'utilisateur à d'autres utilisateurs.
def get_granted_accesses(db: Session, user: User) -> list[Access]:
    return db.query(Access).filter(Access.owner_id == user.id).all()


# Retourne les accès que d'autres utilisateurs ont accordés à l'utilisateur.
def get_received_accesses(db: Session, user: User) -> list[Access]:
    return db.query(Access).filter(Access.grantee_id == user.id).all()


# Accorde un accès (ou met à jour le droit de modification s'il existe déjà).
def grant_access(db: Session, owner: User, grantee: User, can_edit: bool) -> Access:
    access = get_access(db, owner.id, grantee.id)
    if access is None:
        access = Access(owner_id=owner.id, grantee_id=grantee.id, can_edit=can_edit)
        db.add(access)
    else:
        access.can_edit = can_edit
    db.commit()
    db.refresh(access)
    return access


def revoke_access(db: Session, access: Access) -> None:
    db.delete(access)
    db.commit()
