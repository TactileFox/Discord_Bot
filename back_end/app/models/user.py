from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    create_date: datetime
    id: int
    update_date: Optional[datetime] = None
    username: str
