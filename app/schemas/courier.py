from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.application import ApplicationCreateBase, ApplicationReadBase
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
    address: str | None = None
    transport_type: TransportType | None = None