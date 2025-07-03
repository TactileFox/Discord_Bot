from datetime import datetime
from pydantic import BaseModel


class MessageEdit(BaseModel):
    after_content: str
    before_content: str
    create_date: datetime
    id: int
    message_id: int
