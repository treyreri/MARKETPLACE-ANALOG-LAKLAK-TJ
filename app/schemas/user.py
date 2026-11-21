from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.utils.enums import RoleName

PhoneNumber = Annotated [ str, Field(pattern=r"^\+\d{10,15}$", examples=["+992900000000"]) ]
Password = Annotated[str, Field(min_length=6, max_length=128)]

class UserRegister(BaseModel):
    phone_number: PhoneNumber
    password: Password
    password_confirm: str
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)

    @model_validator(mode = "after")
    def check_password_match(self):
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self

class UserUpdate(BaseModel):
    """Profile fields a user may change after registration (spec section 9)."""
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)

    @field_validator("first_name", "last_name")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value is not None else None


class UserLogin(BaseModel):
    phone_number: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    phone_number: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    created_at: datetime
    roles: list[RoleName] = Field(validation_alias="role_names")

class Token(BaseModel):
    access_token: str
    token_type: str= "bearer"


class UserList(BaseModel):
    items: list[UserRead]
    total: int
    limit: int
    offset: int


class UserStatusUpdate(BaseModel):
    is_active: bool
