from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.form import Form, Question
from app.models.response import Response
from app.exceptions import FormNotFoundError, InvalidAnswersError, AccessDeniedError

def validate_answers(questions: List[Question], answers: Dict[int, Any]) -> None:
    question_map = {q.id: q for q in questions}
    errors: List[str] = []

    for q in questions:
        if q.is_required and q.id not in answers:
            errors.append(f"Question '{q.text}' is required")

    for q_id, value in answers.items():
        q = question_map.get(q_id)
        if not q:
            errors.append(f"Question #{q_id} not found")
            continue

        if value is None:
            if q.is_required:
                errors.append(f"Question '{q.text}' is required")
            continue

        if q.question_type == "text":
            if not isinstance(value, str):
                errors.append(f"Invalid answer type for '{q.text}'")
            elif q.is_required and not value.strip():
                errors.append(f"Question '{q.text}' is required")
        elif q.question_type == "radio":
            if not isinstance(value, str) or value not in (q.options or []):
                errors.append(f"Invalid option for '{q.text}'")
        elif q.question_type == "checkbox":
            if not isinstance(value, list) or not all(opt in (q.options or []) for opt in value):
                errors.append(f"Invalid options for '{q.text}'")
            elif q.is_required and len(value) == 0:
                errors.append(f"Question '{q.text}' is required")
        else:
            errors.append(f"Unsupported question type for '{q.text}'")

    if errors:
        raise InvalidAnswersError(errors)

async def submit_response(db: AsyncSession, form_id: int, answers: Dict[int, Any]) -> Response:
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()
    
    if not form:
        raise FormNotFoundError("Form not found")

    q_result = await db.execute(select(Question).where(Question.form_id == form_id))
    questions = q_result.scalars().all()

    validate_answers(questions, answers)

    new_response = Response(form_id=form_id, answers=answers)
    db.add(new_response)
    await db.commit()
    await db.refresh(new_response)
    return new_response

async def get_form_responses(db: AsyncSession, form_id: int, owner_id: int) -> List[Response]:
    form = await db.get(Form, form_id)
    if not form or form.owner_id != owner_id:
        raise AccessDeniedError("Not enough permissions")

    result = await db.execute(
        select(Response).where(Response.form_id == form_id).order_by(Response.submitted_at.desc())
    )
    return result.scalars().all()