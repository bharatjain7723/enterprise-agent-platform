from datetime import datetime

from pydantic import BaseModel


class Memory(BaseModel):
    id: str
    user_id: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime
