from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import Token, UserLogin, UserRead, UserRegister
from app.services import auth_service
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth" , tags = ["Authentication"])
DbSession = Annotated[Session, Depends(get_db)]



@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: DbSession):
    try:
        return auth_service.register_user(db, data)
    except auth_service.PhoneAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number is already registered", )


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: DbSession):
    user = auth_service.authenticate_user(db, data.phone_number, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password", )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",)
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
