from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Attachment(BaseModel):
    create_date: datetime
    delete_date: Optional[datetime] = None
    deleted: int = 0
    file_type: str
    id: int
    message_id: int
    name: str
    update_date: Optional[datetime] = None
    url: str
