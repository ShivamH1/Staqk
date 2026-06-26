import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.models.project import ProjectStatus, WebsiteProject
from app.models.user import Plan, User

_USER_ID = uuid.uuid4()


def _fake_user() -> User:
    return User(
        id=_USER_ID,
        clerk_id="user_test",
        email="t@staqk.com",
        credits=100,
        plan=Plan.free,
    )


def _fake_project(name: str = "My App") -> WebsiteProject:
    now = datetime.now(UTC)
    return WebsiteProject(
        id=uuid.uuid4(),
        user_id=_USER_ID,
        name=name,
        description="",
        tech_stack={"framework": "next"},
        file_tree={},
        status=ProjectStatus.draft,
        created_at=now,
        updated_at=now,
    )


class _FakeDB:
    def begin(self) -> Any:
        @asynccontextmanager
        async def _tx() -> AsyncIterator[None]:
            yield

        return _tx()


@pytest.fixture
def authed_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_current_user] = _fake_user

    async def _db() -> AsyncIterator[_FakeDB]:
        yield _FakeDB()

    app.dependency_overrides[get_db] = _db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_requires_auth() -> None:
    # No dependency override → real auth runs → 401 without a bearer token.
    with TestClient(app) as client:
        assert client.get("/projects").status_code == 401


def test_create_project(authed_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    created = _fake_project("Todo")

    async def fake_create(db: object, user_id: object, name: str, desc: str, stack: object) -> Any:
        created.name = name
        return created

    monkeypatch.setattr("app.services.projects.create_project", fake_create)

    resp = authed_client.post(
        "/projects", json={"name": "Todo", "tech_stack": {"framework": "next"}}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Todo"
    assert body["status"] == "draft"
    assert "file_tree" in body


def test_create_project_rejects_empty_name(authed_client: TestClient) -> None:
    resp = authed_client.post("/projects", json={"name": ""})
    assert resp.status_code == 422  # Field(min_length=1)


def test_list_projects(authed_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    projects = [_fake_project("A"), _fake_project("B")]

    async def fake_list(db: object, user_id: object) -> list[WebsiteProject]:
        return projects

    monkeypatch.setattr("app.services.projects.list_projects", fake_list)

    resp = authed_client.get("/projects")
    assert resp.status_code == 200
    body = resp.json()
    assert [p["name"] for p in body] == ["A", "B"]
    # Summary view must not leak the file tree.
    assert "file_tree" not in body[0]


def test_get_project_found(authed_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _fake_project("Detail")

    async def fake_get(db: object, user_id: object, project_id: object) -> WebsiteProject:
        return project

    monkeypatch.setattr("app.services.projects.get_project", fake_get)

    resp = authed_client.get(f"/projects/{project.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detail"


def test_get_project_missing_returns_404(
    authed_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_get(db: object, user_id: object, project_id: object) -> None:
        return None

    monkeypatch.setattr("app.services.projects.get_project", fake_get)

    resp = authed_client.get(f"/projects/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_project(authed_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_delete(db: object, user_id: object, project_id: object) -> bool:
        return True

    monkeypatch.setattr("app.services.projects.soft_delete_project", fake_delete)

    resp = authed_client.delete(f"/projects/{uuid.uuid4()}")
    assert resp.status_code == 204


def test_delete_missing_returns_404(
    authed_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_delete(db: object, user_id: object, project_id: object) -> bool:
        return False

    monkeypatch.setattr("app.services.projects.soft_delete_project", fake_delete)

    resp = authed_client.delete(f"/projects/{uuid.uuid4()}")
    assert resp.status_code == 404
