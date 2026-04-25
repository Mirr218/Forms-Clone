from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class ResponseBase(BaseModel):
    form_id: int


class ResponseCreate(ResponseBase):
    answers: Dict[str, Any]


class ResponseSubmit(BaseModel):
    answers: Dict[str, Any]


class ResponseResponse(ResponseBase):
    id: int
    form_id: int
    answers: Dict[str, Any]
    submitted_at: datetime

    class Config:
        from_attributes = True
