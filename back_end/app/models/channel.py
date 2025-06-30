from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from models.guild import Guild


class Channel(BaseModel):
    category: str
    channel_type: int
    create_date: datetime
    guild: Guild
    id: int
    name: str
    nsfw: int
    update_date: Optional[datetime] = None
