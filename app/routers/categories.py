from fastapi import APIRouter, Depends, HTTPException, status
from app.database import DbSession
from app.dependencies.language import CurrentLanguage
from app.dependencies.permissions import require_admin
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category_service
from app.services.category_service import CategoryNameTakenError, CategoryNotFoundError

router = APIRouter(prefix="/categories", tags=["Categories"])

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
NAME_TAKEN = HTTPException(status.HTTP_409_CONFLICT, "Category name already exists")


@router.get("", response_model=list[CategoryRead])
def list_categories(db: DbSession, lang: CurrentLanguage):
    return [CategoryRead.from_model(c, lang) for c in category_service.list_categories(db)]


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: DbSession, lang: CurrentLanguage):
    try:
        return CategoryRead.from_model(category_service.get_category(db, category_id), lang)
    except CategoryNotFoundError:
        raise NOT_FOUND


@router.post( "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)], )
def create_category(data: CategoryCreate, db: DbSession, lang: CurrentLanguage):
    try:
        return CategoryRead.from_model(category_service.create_category(db, data), lang)
    except CategoryNameTakenError:
        raise NAME_TAKEN


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    dependencies=[Depends(require_admin)], )
def update_category(
    category_id: int, data: CategoryUpdate, db: DbSession, lang: CurrentLanguage ):
    try:
        category = category_service.update_category(db, category_id, data)
        return CategoryRead.from_model(category, lang)
    except CategoryNotFoundError:
        raise NOT_FOUND
    except CategoryNameTakenError:
        raise NAME_TAKEN


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)], )
def delete_category(category_id: int, db: DbSession):
    try:
        category_service.delete_category(db, category_id)
    except CategoryNotFoundError:
        raise NOT_FOUND


#dependencies=[Depends(require_admin)] включает проверку прав, но не передаёт пользователя в функцию. 
#Здесь он не нужен, достаточно убедиться, что запрос делает админ