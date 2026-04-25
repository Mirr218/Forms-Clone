from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db import get_db
from app.exceptions import AccessDeniedError, FormNotFoundError, InvalidAnswersError
from app.schemas.response import ResponseResponse, ResponseSubmit
from app.service import get_form_responses, submit_response

router = APIRouter(prefix="/api/forms", tags=["submissions"])


@router.post(
    "/{form_id}/responses",
    response_model=ResponseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_form_response(
    form_id: int,
    payload: ResponseSubmit,
    db: AsyncSession = Depends(get_db),
) -> ResponseResponse:
    try:
        return await submit_response(db, form_id, payload.answers)
    except FormNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except InvalidAnswersError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/{form_id}/responses", response_model=List[ResponseResponse])
async def list_form_responses(
    form_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> List[ResponseResponse]:
    try:
        responses = await get_form_responses(db, form_id, user_id)
        return [ResponseResponse.model_validate(response) for response in responses]
    except AccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
