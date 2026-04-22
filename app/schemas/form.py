from typing import List, Literal, Optional

from pydantic import BaseModel

from .user import UserResponse

QuestionType = Literal["text", "radio", "checkbox"]


class QuestionBase(BaseModel):
    form_id: int
    question_type: str
    text: str
    is_required: bool = False
    options: Optional[List[str]] = None
    position: int


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_type: Optional[str] = None
    text: Optional[str] = None
    is_required: Optional[bool] = None
    options: Optional[List[str]] = None
    position: Optional[int] = None


class QuestionResponse(QuestionBase):
    id: int

    class Config:
        from_attributes = True


class FormBase(BaseModel):
    title: str
    description: Optional[str] = None


class FormCreate(FormBase):
    questions: List[QuestionCreate] = []


class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class FormResponse(FormBase):
    id: int
    owner_id: int
    owner: UserResponse
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True
