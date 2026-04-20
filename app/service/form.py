from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.form import Form, Question
from app.schemas.form import FormCreate
from app.exceptions import FormNotFoundError, AccessDeniedError

async def create_form(db: AsyncSession, form_data: FormCreate, owner_id: int) -> Form:
    new_form = Form(
        title=form_data.title,
        description=form_data.description,
        owner_id=owner_id
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
            position=q_data.position
        )
        db.add(question)

    await db.commit()
    await db.refresh(new_form)
    return new_form

async def get_form_by_id(db: AsyncSession, form_id: int) -> Form:
    result = await db.execute(
        select(Form).where(Form.id == form_id).options(selectinload(Form.questions))
    )
    form = result.scalar_one_or_none()
    if not form:
        raise FormNotFoundError("Form not found")
    return form

async def update_form(db: AsyncSession, form_id: int, owner_id: int, form_data: FormCreate) -> Form:
    form = await get_form_by_id(db, form_id)
    
    if form.owner_id != owner_id:
        raise AccessDeniedError("Not enough permissions")

    form.title = form_data.title
    form.description = form_data.description
    form.questions.clear()
    
    await db.flush()
    
    for q_data in form_data.questions:
        form.questions.append(Question(
            form_id=form.id,
            question_type=q_data.question_type,
            text=q_data.text,
            is_required=q_data.is_required,
            options=q_data.options,
            position=q_data.position
        ))

    await db.commit()
    await db.refresh(form)
    return form

async def delete_form(db: AsyncSession, form_id: int, owner_id: int) -> None:
    form = await get_form_by_id(db, form_id)
    
    if form.owner_id != owner_id:
        raise AccessDeniedError("Not enough permissions")

    await db.delete(form)
    await db.commit()