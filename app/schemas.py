from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class SymptomChatRequest(BaseModel):
    message: str = Field(..., min_length=2)
    conversation: list[ChatMessage] = Field(default_factory=list)


class DoctorOut(BaseModel):
    doctor_id: int
    full_name: str
    email: str | None = None
    phone_no: str | None = None
    status: str | None = None
    experience: str | None = None
    short_desc: str | None = None
    gender: str | None = None
    specialization: list[str] = Field(default_factory=list)


class SymptomChatResponse(BaseModel):
    reply: str
    suggested_specialization: str | None = None
    doctors: list[DoctorOut] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
