from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Guild(BaseModel):
    create_date: datetime
    description: str
    id: int
    name: str
    update_date: Optional[datetime] = None
