from datetime import datetime
from app.models.enums import ChannelType
from pydantic import BaseModel
from typing import Optional
from app.models.guild import Guild


class Channel(BaseModel):
    category: str
    channel_type: ChannelType
    create_date: datetime
    guild: Guild
    id: int
    name: str
    nsfw: int
    update_date: Optional[datetime] = None
