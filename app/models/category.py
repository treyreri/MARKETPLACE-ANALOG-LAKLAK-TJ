from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.enums import Language

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name_ru: Mapped[str] = mapped_column(String(100), unique=True)
    name_en: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)

    def get_name(self, lang: Language) -> str:
        return self.name_en if lang == Language.EN else self.name_ru


    