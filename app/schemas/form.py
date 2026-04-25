from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .user import UserResponse

QuestionType = Literal["text", "radio", "checkbox"]


class QuestionBase(BaseModel):
    question_type: QuestionType
    text: str
    is_required: bool = False
    options: Optional[List[str]] = None
    position: int


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_type: Optional[QuestionType] = None
    text: Optional[str] = None
    is_required: Optional[bool] = None
    options: Optional[List[str]] = None
    position: Optional[int] = None


class QuestionResponse(QuestionBase):
    id: int
    form_id: int

    class Config:
        from_attributes = True


class FormBase(BaseModel):
    title: str
    description: Optional[str] = None


class FormCreate(FormBase):
    questions: List[QuestionCreate] = Field(default_factory=list)


class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[QuestionCreate]] = None


class FormResponse(FormBase):
    id: int
    owner_id: int
    owner: UserResponse
    questions: List[QuestionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
