from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.recipe import Recipe

# Table des utilisateurs
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Stocke le mot de passe haché, jamais en clair
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Un utilisateur peut posséder plusieurs recettes
    recipes: Mapped[list["Recipe"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


# Table des accès : un propriétaire partage ses recettes avec un autre utilisateur
class Access(Base):
    __tablename__ = "accesses"
    __table_args__ = (UniqueConstraint("owner_id", "grantee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    grantee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    # False = lecture seule, True = lecture et modification
    can_edit: Mapped[bool] = mapped_column(default=False, nullable=False)
