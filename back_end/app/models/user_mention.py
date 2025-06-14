from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.user import User


class UserMention(BaseModel):
    author_id: int
    create_date: datetime
    delete_date: Optional[datetime] = None
    deleted: int = 0
    id: int
    message_id: int
    update_date: Optional[datetime] = None
    recipient: User
