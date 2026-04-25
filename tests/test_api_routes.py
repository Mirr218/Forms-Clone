from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api import api_router
from app.core.security import get_current_user_id
from app.db import Base, get_db


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


@pytest_asyncio.fixture
async def api_client(
    db_session: AsyncSession,
) -> AsyncGenerator[tuple[AsyncClient, dict[str, int]], None]:
    app = FastAPI()
    app.include_router(api_router)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    current_user = {"id": 1}

    async def override_get_current_user_id() -> int:
        return current_user["id"]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, current_user

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_auth_register_and_login(
    api_client: tuple[AsyncClient, dict[str, int]],
) -> None:
    client, _ = api_client

    register_response = await client.post(
        "/api/auth/register",
        json={"email": "auth@example.com", "password": "secret123"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "auth@example.com"

    login_response = await client.post(
        "/api/auth/login",
        json={"email": "auth@example.com", "password": "secret123"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


@pytest.mark.asyncio
async def test_forms_crud_flow(api_client: tuple[AsyncClient, dict[str, int]]) -> None:
    client, current_user = api_client

    register_response = await client.post(
        "/api/auth/register",
        json={"email": "owner@example.com", "password": "secret123"},
    )
    owner_id = register_response.json()["id"]
    current_user["id"] = owner_id

    create_response = await client.post(
        "/api/forms/",
        json={
            "title": "API form",
            "description": "Initial description",
            "questions": [
                {
                    "question_type": "text",
                    "text": "Name",
                    "is_required": True,
                    "position": 1,
                }
            ],
        },
    )
    assert create_response.status_code == 201
    form_id = create_response.json()["id"]

    list_response = await client.get("/api/forms/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == form_id

    update_response = await client.put(
        f"/api/forms/{form_id}",
        json={"title": "API form updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "API form updated"
    assert update_response.json()["description"] == "Initial description"

    delete_response = await client.delete(f"/api/forms/{form_id}")
    assert delete_response.status_code == 204

    get_deleted_response = await client.get(f"/api/forms/{form_id}")
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_submissions_submit_and_list_with_owner_access(
    api_client: tuple[AsyncClient, dict[str, int]],
) -> None:
    client, current_user = api_client

    register_response = await client.post(
        "/api/auth/register",
        json={"email": "submit-owner@example.com", "password": "secret123"},
    )
    owner_id = register_response.json()["id"]
    current_user["id"] = owner_id

    form_response = await client.post(
        "/api/forms/",
        json={
            "title": "Survey",
            "questions": [
                {
                    "question_type": "text",
                    "text": "Your name",
                    "is_required": True,
                    "position": 1,
                }
            ],
        },
    )
    form = form_response.json()
    question_id = str(form["questions"][0]["id"])

    submit_response = await client.post(
        f"/api/forms/{form['id']}/responses",
        json={"answers": {question_id: "Alice"}},
    )
    assert submit_response.status_code == 201
    assert submit_response.json()["form_id"] == form["id"]

    list_response = await client.get(f"/api/forms/{form['id']}/responses")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["answers"][question_id] == "Alice"


@pytest.mark.asyncio
async def test_submissions_list_forbidden_for_non_owner(
    api_client: tuple[AsyncClient, dict[str, int]],
) -> None:
    client, current_user = api_client

    owner_response = await client.post(
        "/api/auth/register",
        json={"email": "owner-forbidden@example.com", "password": "secret123"},
    )
    owner_id = owner_response.json()["id"]
    current_user["id"] = owner_id

    form_response = await client.post(
        "/api/forms/",
        json={"title": "Private form", "questions": []},
    )
    form_id = form_response.json()["id"]

    stranger_response = await client.post(
        "/api/auth/register",
        json={"email": "stranger-forbidden@example.com", "password": "secret123"},
    )
    current_user["id"] = stranger_response.json()["id"]

    list_response = await client.get(f"/api/forms/{form_id}/responses")
    assert list_response.status_code == 403
