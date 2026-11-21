from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.utils.enums import RoleName

def require_role(role: RoleName):
    def checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not current_user.has_role(role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not enough permissions" ,)
        return current_user
    return checker
require_admin = require_role(RoleName.ADMIN)
AdminUser = Annotated[User, Depends(require_admin)]

#require_role — это фабрика dependency: она возвращает функцию-проверку для конкретной роли. 
#Позже так же сделаем require_role(RoleName.SELLER) и require_role(RoleName.COURIER)