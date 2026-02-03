from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Reservation(BaseModel):
    reservationId: int = Field(...)
    userId: int = Field(...)
    businessId: int = Field(...)
    businessName: str = Field(default="")
    date: str = Field(...)  # ISO date string YYYY-MM-DD
    time: str = Field(...)  # HH:MM format
    partySize: int = Field(..., ge=1, le=50)
    status: str = Field(default="confirmed")  # confirmed, cancelled, completed
    notes: Optional[str] = Field(default=None, max_length=500)
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reminderSent: bool = Field(default=False)


class Notification(BaseModel):
    notificationId: int = Field(...)
    userId: int = Field(...)
    type: str = Field(...)  # reservation_reminder, reservation_confirmed, reservation_cancelled
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=500)
    relatedId: Optional[int] = Field(default=None)
    read: bool = Field(default=False)
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
