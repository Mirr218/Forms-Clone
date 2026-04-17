from datetime import datetime
from typing import Any, List

from pydantic import BaseModel


class AnswerSchema(BaseModel):
    question_id: int
    answer_value: Any


class ResponseBase(BaseModel):
    form_id: int


class ResponseCreate(ResponseBase):
    answers: List[AnswerSchema]


class ResponseResponse(ResponseBase):
    id: int
    form_id: int
    answers: List[AnswerSchema]
    submitted_at: datetime

    class Config:
        from_attributes = True
