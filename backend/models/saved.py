from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Collection(BaseModel):
    collectionId: int = Field(...)
    userId: int = Field(...)
    name: str = Field(..., min_length=1, max_length=100)
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SavedBusiness(BaseModel):
    savedId: int = Field(...)
    userId: int = Field(...)
    businessId: int = Field(...)
    collectionId: int = Field(...)
    dateSaved: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
