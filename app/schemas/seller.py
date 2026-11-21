from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import not_nullable
from app.schemas.user import PhoneNumber
from app.utils.enums import ApplicationStatus
from app.schemas.application import ApplicationCreateBase, ApplicationReadBase


class SellerApplicationCreate(ApplicationCreateBase):
    store_name: str = Field(min_length=1, max_length=100)
    store_description: str | None = None
    category_id: int | None = None


class SellerApplicationRead(ApplicationReadBase):
    store_name: str
    store_description: str | None
    category_id: int | None


class SellerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    store_name: str
    store_description: str | None
    address: str
    phone_number: str
    created_at: datetime


class SellerProfileUpdate(BaseModel):
    store_name: str | None = Field(default=None, min_length=1, max_length=100)
    store_description: str | None = None
    address: str | None = Field(default=None, min_length=1, max_length=255)
    phone_number: PhoneNumber | None = None

    _not_null = not_nullable("store_name", "address", "phone_number")