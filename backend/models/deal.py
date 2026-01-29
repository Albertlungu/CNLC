from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Deal(BaseModel):
    dealId: int = Field(...)
    businessId: int = Field(...)
    createdByUserId: Optional[int] = Field(default=None)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    discountType: str = Field(...)  # "percentage", "fixed", "bogo", "other"
    discountValue: Optional[float] = Field(default=None)
    expiresAt: Optional[str] = Field(default=None)
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    isActive: bool = Field(default=True)
    source: str = Field(default="manual")  # "manual" or "scraped"
    sourceUrl: Optional[str] = Field(default=None)


class SavedDeal(BaseModel):
    savedDealId: int = Field(...)
    userId: int = Field(...)
    dealId: int = Field(...)
    savedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
