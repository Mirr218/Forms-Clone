from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel

class ResponseBase(BaseModel):
    form_id: int


class ResponseCreate(ResponseBase):
    answers: Dict[int, Any]


class ResponseResponse(ResponseBase):
    id: int
    form_id: int
    answers: Dict[int, Any]
    submitted_at: datetime

    class Config:
        from_attributes = True
