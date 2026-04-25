from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.exceptions import AccessDeniedError, FormNotFoundError
from app.models import Form, Question, User
from app.schemas.form import FormCreate, FormUpdate, QuestionCreate
from app.service.form import (
    create_form,
    delete_form,
    get_form_by_id,
    get_user_forms,
    update_form,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, autoflush=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _create_user(session: AsyncSession, email: str) -> User:
    user = User(email=email, hashed_password="hash")
    session.add(user)
    await session.flush()
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_create_form_creates_questions(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner@example.com")
    payload = FormCreate(
        title="Feedback Form",
        description="Collect feedback",
        questions=[
            QuestionCreate(
                question_type="text",
                text="Your name",
                is_required=True,
                position=1,
            ),
            QuestionCreate(
                question_type="radio",
                text="Rate us",
                is_required=False,
                options=["Good", "Bad"],
                position=2,
            ),
        ],
    )

    created = await create_form(db_session, payload, owner.id)

    assert created.id is not None
    loaded = await get_form_by_id(db_session, created.id)
    assert loaded.title == "Feedback Form"
    assert len(loaded.questions) == 2
    assert loaded.questions[0].text == "Your name"
    assert loaded.questions[1].options == ["Good", "Bad"]


@pytest.mark.asyncio
async def test_get_form_by_id_raises_for_missing_form(db_session: AsyncSession) -> None:
    with pytest.raises(FormNotFoundError):
        await get_form_by_id(db_session, 9999)


@pytest.mark.asyncio
async def test_update_form_updates_fields_and_replaces_questions(
    db_session: AsyncSession,
) -> None:
    owner = await _create_user(db_session, "owner-update@example.com")
    initial = await create_form(
        db_session,
        FormCreate(
            title="Old title",
            description="Old description",
            questions=[
                QuestionCreate(
                    question_type="text",
                    text="Old question",
                    position=1,
                )
            ],
        ),
        owner.id,
    )

    updated = await update_form(
        db_session,
        initial.id,
        owner.id,
        FormUpdate(
            title="New title",
            description="New description",
            questions=[
                QuestionCreate(
                    question_type="checkbox",
                    text="New question",
                    options=["A", "B"],
                    is_required=True,
                    position=1,
                )
            ],
        ),
    )

    assert updated.title == "New title"
    assert updated.description == "New description"
    reloaded = await get_form_by_id(db_session, initial.id)
    assert len(reloaded.questions) == 1
    assert reloaded.questions[0].text == "New question"
    assert reloaded.questions[0].question_type == "checkbox"

    questions_result = await db_session.execute(
        select(Question).where(Question.form_id == initial.id)
    )
    questions = list(questions_result.scalars().all())
    assert len(questions) == 1
    assert questions[0].text == "New question"


@pytest.mark.asyncio
async def test_update_form_raises_for_non_owner(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner-access-update@example.com")
    stranger = await _create_user(db_session, "stranger-access-update@example.com")
    created = await create_form(
        db_session,
        FormCreate(title="Protected form"),
        owner.id,
    )

    with pytest.raises(AccessDeniedError):
        await update_form(
            db_session,
            created.id,
            stranger.id,
            FormUpdate(title="Should fail"),
        )


@pytest.mark.asyncio
async def test_delete_form_removes_form(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner-delete@example.com")
    created = await create_form(
        db_session,
        FormCreate(title="To delete"),
        owner.id,
    )

    await delete_form(db_session, created.id, owner.id)

    with pytest.raises(FormNotFoundError):
        await get_form_by_id(db_session, created.id)


@pytest.mark.asyncio
async def test_delete_form_raises_for_non_owner(db_session: AsyncSession) -> None:
    owner = await _create_user(db_session, "owner-access-delete@example.com")
    stranger = await _create_user(db_session, "stranger-access-delete@example.com")
    created = await create_form(
        db_session,
        FormCreate(title="Protected form"),
        owner.id,
    )

    with pytest.raises(AccessDeniedError):
        await delete_form(db_session, created.id, stranger.id)


@pytest.mark.asyncio
async def test_get_user_forms_returns_only_owner_sorted_by_id_desc(
    db_session: AsyncSession,
) -> None:
    owner = await _create_user(db_session, "owner-forms@example.com")
    other = await _create_user(db_session, "other-forms@example.com")

    await create_form(db_session, FormCreate(title="Owner first"), owner.id)
    await create_form(db_session, FormCreate(title="Other form"), other.id)
    await create_form(db_session, FormCreate(title="Owner second"), owner.id)

    owner_forms = await get_user_forms(db_session, owner.id)

    assert len(owner_forms) == 2
    assert [form.title for form in owner_forms] == ["Owner second", "Owner first"]

    ids_result = await db_session.execute(
        select(Form.id).where(Form.owner_id == owner.id)
    )
    owner_ids = list(ids_result.scalars().all())
    assert [form.id for form in owner_forms] == sorted(owner_ids, reverse=True)
