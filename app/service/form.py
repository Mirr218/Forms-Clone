from typing import List, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import AccessDeniedError, FormNotFoundError
from app.models.form import Form, Question
from app.schemas.form import FormCreate, FormUpdate


async def create_form(db: AsyncSession, form_data: FormCreate, owner_id: int) -> Form:
    new_form = Form(
        title=form_data.title, description=form_data.description, owner_id=owner_id
    )
    db.add(new_form)

    await db.flush()

    for q_data in form_data.questions:
        question = Question(
            form_id=new_form.id,
            question_type=q_data.question_type,
            text=q_data.text,
            is_required=q_data.is_required,
            options=q_data.options,
            position=q_data.position,
        )
        db.add(question)

    await db.commit()
    await db.refresh(new_form)
    return new_form


async def get_form_by_id(db: AsyncSession, form_id: int) -> Form:
    result = await db.execute(
        select(Form)
        .where(Form.id == form_id)
        .options(selectinload(Form.owner), selectinload(Form.questions))
    )
    form = result.scalar_one_or_none()
    if not form:
        raise FormNotFoundError("Form not found")
    return form


async def update_form(
    db: AsyncSession, form_id: int, owner_id: int, form_data: FormUpdate
) -> Form:
    form = await get_form_by_id(db, form_id)

    if form.owner_id != owner_id:
        raise AccessDeniedError("Not enough permissions")

    if form_data.title is not None:
        form.title = form_data.title
    if form_data.description is not None:
        form.description = form_data.description

    if form_data.questions is not None:
        form.questions.clear()
        await db.flush()
        for q_data in form_data.questions:
            form.questions.append(
                Question(
                    form_id=form.id,
                    question_type=q_data.question_type,
                    text=q_data.text,
                    is_required=q_data.is_required,
                    options=q_data.options,
                    position=q_data.position,
                )
            )

    await db.commit()
    await db.refresh(form)
    return form


async def delete_form(db: AsyncSession, form_id: int, owner_id: int) -> None:
    form = await get_form_by_id(db, form_id)

    if form.owner_id != owner_id:
        raise AccessDeniedError("Not enough permissions")

    await db.delete(form)
    await db.commit()


async def get_user_forms(db: AsyncSession, owner_id: int) -> List[Form]:
    result = await db.execute(
        select(Form)
        .where(Form.owner_id == owner_id)
        .options(selectinload(Form.owner), selectinload(Form.questions))
        .order_by(Form.id.desc())
    )
    return list(result.scalars().all())


async def get_all_forms_sorted(
    db: AsyncSession,
    sort_by: Literal["title", "created_at"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> List[Form]:
    sort_columns = {"title": Form.title, "created_at": Form.created_at}
    sort_column = sort_columns[sort_by]
    order_clause = sort_column.asc() if order == "asc" else sort_column.desc()

    result = await db.execute(
        select(Form)
        .options(selectinload(Form.owner), selectinload(Form.questions))
        .order_by(order_clause)
    )
    return list(result.scalars().all())


async def get_all_forms_filtered_by_title(
    db: AsyncSession, title_contains: str
) -> List[Form]:
    result = await db.execute(
        select(Form)
        .where(Form.title.ilike(f"%{title_contains.strip()}%"))
        .options(selectinload(Form.owner), selectinload(Form.questions))
        .order_by(Form.created_at.desc())
    )
    return list(result.scalars().all())
