from datetime import datetime
from pydantic import BaseModel
from typing import Optional
# Emoji will have it's own model at a later date


class Reaction(BaseModel):
    emoji: str
    create_date: datetime
    delete_date: Optional[datetime] = None
    deleted: int = 0
    id: int
    message_id: int
    self_react: int
    user_id: int
