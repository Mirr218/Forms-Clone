from typing import Any, Dict, List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AccessDeniedError, FormNotFoundError, InvalidAnswersError
from app.models.form import Form, Question
from app.models.response import Response


def normalize_answer_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    errors: List[str] = []

    for raw_key, value in answers.items():
        if not isinstance(raw_key, str):
            errors.append(f"Question key '{raw_key}' has invalid type")
            continue
        key = raw_key.strip()
        if not key:
            errors.append("Question key cannot be empty")
            continue

        if key in normalized:
            errors.append(f"Duplicate question key after normalization: '{key}'")
            continue

        normalized[key] = value

    if errors:
        raise InvalidAnswersError(errors)

    return normalized


def validate_answers(questions: Sequence[Question], answers: Dict[str, Any]) -> None:
    question_map = {str(q.id): q for q in questions}
    errors: List[str] = []

    for q in questions:
        if q.is_required and str(q.id) not in answers:
            errors.append(f"Question '{q.text}' is required")

    for q_id, value in answers.items():
        question = question_map.get(q_id)
        if not question:
            errors.append(f"Question #{q_id} not found")
            continue

        if value is None:
            if question.is_required:
                errors.append(f"Question '{question.text}' is required")
            continue

        if question.question_type == "text":
            if not isinstance(value, str):
                errors.append(f"Invalid answer type for '{question.text}'")
            elif question.is_required and not value.strip():
                errors.append(f"Question '{question.text}' is required")
        elif question.question_type == "radio":
            if not isinstance(value, str) or value not in (question.options or []):
                errors.append(f"Invalid option for '{question.text}'")
        elif question.question_type == "checkbox":
            if not isinstance(value, list) or not all(
                opt in (question.options or []) for opt in value
            ):
                errors.append(f"Invalid options for '{question.text}'")
            elif question.is_required and len(value) == 0:
                errors.append(f"Question '{question.text}' is required")
        else:
            errors.append(f"Unsupported question type for '{question.text}'")

    if errors:
        raise InvalidAnswersError(errors)


async def submit_response(
    db: AsyncSession, form_id: int, answers: Dict[str, Any]
) -> Response:
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()

    if not form:
        raise FormNotFoundError("Form not found")

    q_result = await db.execute(select(Question).where(Question.form_id == form_id))
    questions = q_result.scalars().all()

    normalized_answers = normalize_answer_keys(answers)
    validate_answers(questions, normalized_answers)

    new_response = Response(form_id=form_id, answers=normalized_answers)
    db.add(new_response)
    await db.commit()
    await db.refresh(new_response)
    return new_response


async def get_form_responses(
    db: AsyncSession, form_id: int, owner_id: int
) -> List[Response]:
    form = await db.get(Form, form_id)
    if not form or form.owner_id != owner_id:
        raise AccessDeniedError("Not enough permissions")

    result = await db.execute(
        select(Response)
        .where(Response.form_id == form_id)
        .order_by(Response.submitted_at.desc())
    )
    return list(result.scalars().all())
