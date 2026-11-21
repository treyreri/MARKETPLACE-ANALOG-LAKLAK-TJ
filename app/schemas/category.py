from pydantic import BaseModel, Field
from app.models.category import Category
from app.utils.enums import Language


class CategoryCreate(BaseModel):
    name_ru: str = Field(min_length=1, max_length=100)
    name_en: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CategoryUpdate(BaseModel):
    name_ru: str | None = Field(default=None, min_length=1, max_length=100)
    name_en: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class CategoryRead(BaseModel):
    id: int
    name: str
    name_ru: str
    name_en: str
    description: str | None

    @classmethod
    def from_model(cls, category: Category, lang: Language) -> "CategoryRead":
        return cls(
            id=category.id,
            name=category.get_name(lang),
            name_ru=category.name_ru,
            name_en=category.name_en,
            description=category.description, )