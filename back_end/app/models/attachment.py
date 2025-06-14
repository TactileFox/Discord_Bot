from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.enums import FileType


class Attachment(BaseModel):
    create_date: datetime
    delete_date: Optional[datetime] = None
    deleted: int = 0
    file_type: FileType
    id: int
    message_id: int
    name: str
    update_date: Optional[datetime] = None
    url: str
