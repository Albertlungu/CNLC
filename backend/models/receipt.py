from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Receipt(BaseModel):
    receiptId: int = Field(...)
    userId: int = Field(...)
    businessId: int = Field(...)
    amount: float = Field(..., gt=0)
    receiptImagePath: str = Field(...)
    submittedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    verified: bool = Field(default=False)


class TrendingPoints(BaseModel):
    businessId: int = Field(...)
    totalSpent: float = Field(default=0.0)
    points: float = Field(default=0.0)
    receiptCount: int = Field(default=0)
