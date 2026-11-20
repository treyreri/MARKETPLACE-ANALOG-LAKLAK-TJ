from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] ,
        db: Annotated[Session, Depends(get_db)] ,) -> User: 
    unauthorized = HTTPException(
        statsu_code = status.HTTP_401_UNAUTHORIZED,
        detail = "could not vslidste credentials" ,
        headers= {"WWW-Authenticate" : "Bearer"} , )
    if credentials is None:
        raise unauthorized

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user
