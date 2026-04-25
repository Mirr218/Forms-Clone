from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models import Form, User
from app.service.form import get_all_forms_filtered_by_title, get_all_forms_sorted


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


async def _seed_forms(session: AsyncSession) -> None:
    user = User(email="owner@example.com", hashed_password="hash")
    session.add(user)
    await session.flush()

    now = datetime.now(timezone.utc)
    forms = [
        Form(
            title="Customer Survey",
            description=None,
            owner_id=user.id,
            created_at=now - timedelta(days=2),
        ),
        Form(
            title="Alpha Intake",
            description=None,
            owner_id=user.id,
            created_at=now - timedelta(days=1),
        ),
        Form(
            title="beta Feedback",
            description=None,
            owner_id=user.id,
            created_at=now,
        ),
    ]
    session.add_all(forms)
    await session.commit()


@pytest.mark.asyncio
async def test_get_all_forms_sorted_by_title_asc(db_session: AsyncSession) -> None:
    await _seed_forms(db_session)

    forms = await get_all_forms_sorted(db_session, sort_by="title", order="asc")

    assert [form.title for form in forms] == [
        "Alpha Intake",
        "Customer Survey",
        "beta Feedback",
    ]


@pytest.mark.asyncio
async def test_get_all_forms_sorted_by_created_at_desc(
    db_session: AsyncSession,
) -> None:
    await _seed_forms(db_session)

    forms = await get_all_forms_sorted(db_session, sort_by="created_at", order="desc")

    assert [form.title for form in forms] == [
        "beta Feedback",
        "Alpha Intake",
        "Customer Survey",
    ]


@pytest.mark.asyncio
async def test_get_all_forms_filtered_by_title_case_insensitive(
    db_session: AsyncSession,
) -> None:
    await _seed_forms(db_session)

    forms = await get_all_forms_filtered_by_title(db_session, "  SURVEY ")

    assert [form.title for form in forms] == ["Customer Survey"]


@pytest.mark.asyncio
async def test_get_all_forms_filtered_by_title_empty_string_returns_all(
    db_session: AsyncSession,
) -> None:
    await _seed_forms(db_session)

    forms = await get_all_forms_filtered_by_title(db_session, "   ")

    assert len(forms) == 3
    assert [form.title for form in forms] == [
        "beta Feedback",
        "Alpha Intake",
        "Customer Survey",
    ]
