from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator
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