from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.user import User

# Table des recettes
class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False)
    servings: Mapped[int] = mapped_column(nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # Une recette appartient à un seul utilisateur
    owner: Mapped["User"] = relationship(back_populates="recipes")
