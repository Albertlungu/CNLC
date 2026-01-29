 from pydantic import BaseModel, Field
from datetime import datetime


class FriendRequest(BaseModel):
    requestId: int = Field(...)
    fromUserId: int = Field(...)
    toUserId: int = Field(...)
    status: str = Field(default="pending")  # "pending", "accepted", "rejected"
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Friendship(BaseModel):
    friendshipId: int = Field(...)
    user1Id: int = Field(...)
    user2Id: int = Field(...)
    since: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
