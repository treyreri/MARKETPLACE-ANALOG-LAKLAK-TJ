from typing import Annotated
from fastapi import Depends, Header, Query
from app.utils.enums import Language


def get_language(
    lang: Annotated[Language | None, Query()] = None,
    accept_language: Annotated[str | None, Header()] = None, ) -> Language:
    if lang is not None:
        return lang
    if accept_language and accept_language.lower().startswith("en"):
        return Language.EN
    return Language.RU

CurrentLanguage = Annotated[Language, Depends(get_language)]