from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from models.channel import Channel
from models.guild import Guild
from models.user import User
from models.attachment import Attachment
from models.user_mention import UserMention


class Message(BaseModel):
    attachments: Optional[List[Attachment]] = None
    author: User
    channel: Channel
    content: str
    create_date: datetime
    delete_date: Optional[datetime] = None
    deleted: int = 0
    edited: int = 0
    guild: Guild
    id: int
    update_date: Optional[datetime] = None
    user_mentions: Optional[List[UserMention]] = None
