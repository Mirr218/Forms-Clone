from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db import get_db
from app.exceptions import AccessDeniedError, FormNotFoundError
from app.schemas.form import FormCreate, FormResponse
from app.service import (
    create_form,
    delete_form,
    get_form_by_id,
    get_user_forms,
    update_form,
)

router = APIRouter(prefix="/api/forms", tags=["forms"])


@router.post("/", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_new_form(
    form_in: FormCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> FormResponse:
    return await create_form(db, form_in, user_id)


@router.get("/", response_model=List[FormResponse])
async def list_my_forms(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> List[FormResponse]:
    forms = await get_user_forms(db, user_id)
    return [FormResponse.model_validate(form) for form in forms]


@router.get("/{form_id}", response_model=FormResponse)
async def get_one_form(
    form_id: int, db: AsyncSession = Depends(get_db)
) -> FormResponse:
    try:
        return await get_form_by_id(db, form_id)
    except FormNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put("/{form_id}", response_model=FormResponse)
async def update_one_form(
    form_id: int,
    form_in: FormCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> FormResponse:
    try:
        return await update_form(db, form_id, user_id, form_in)
    except FormNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_one_form(
    form_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    try:
        await delete_form(db, form_id, user_id)
    except FormNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
