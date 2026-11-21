from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister
from app.utils.security import hash_password, verify_password

class PhoneAlreadyRegisteredError(Exception):
    pass

def get_user_by_phone(db: Session, phone_number: str) -> User | None:
    return db.scalar(select(User).where (User.phone_number == phone_number) )

def register_user(db: Session, data: UserRegister) -> User:
    if get_user_by_phone(db, data.phone_number):
        raise PhoneAlreadyRegisteredError
    user = User( 
        phone_number=data.phone_number,
        password_hash = hash_password(data.password),
        first_name = data.first_name,
        last_name = data.last_name , )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request registered the same phone after our check
        db.rollback()
        raise PhoneAlreadyRegisteredError
    db.refresh(user)
    return user

def authenticate_user(db: Session, phone_number: str, password: str) -> User | None:
    user = get_user_by_phone(db, phone_number)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user