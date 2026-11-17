from pydantic import BaseModel, Field

# Schemas pour les recettes
class RecipeBase(BaseModel):
    title : str
    duration : int
    servings : int


class RecipeCreate(RecipeBase):
    title: str = Field(min_length=3, max_length=100)
    duration: int = Field(gt=0)
    servings: int = Field(gt=0)

class RecipeResponse(RecipeBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
