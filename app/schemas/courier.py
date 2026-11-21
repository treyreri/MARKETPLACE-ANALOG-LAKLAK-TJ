from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.application import ApplicationCreateBase, ApplicationReadBase
from app.schemas.common import not_nullable
from app.schemas.user import PhoneNumber
from app.utils.enums import TransportType


class CourierApplicationCreate(ApplicationCreateBase):
    transport_type: TransportType
    experience: str | None = None


class CourierApplicationRead(ApplicationReadBase):
    transport_type: TransportType
    experience: str | None


class CourierProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phone_number: str
    address: str
    transport_type: TransportType
    created_at: datetime


class CourierProfileUpdate(BaseModel):
    phone_number: PhoneNumber | None = None
    address: str | None = Field(default=None, min_length=1, max_length=255)
    transport_type: TransportType | None = None

    _not_null = not_nullable("phone_number", "address", "transport_type")