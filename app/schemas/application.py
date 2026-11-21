from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user import PhoneNumber
from app.utils.enums import ApplicationStatus


class ApplicationCreateBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    phone_number: PhoneNumber
    address: str = Field(min_length=1, max_length=255)
    additional_info: str | None = None


class ApplicationReadBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    first_name: str
    last_name: str
    phone_number: str
    address: str
    additional_info: str | None
    status: ApplicationStatus
    admin_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None


class ApplicationReview(BaseModel):
    status: Literal[ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]
    admin_comment: str | None = Field(default=None, max_length=1000)

#Literal разрешает только approved и rejected. 
#Отправить {"status": "pending"} нельзя, Pydantic сразу вернёт 422