"""
Tests for data models — TaskItem, ApiResponse, CookieItem, ProjectItem, TokenItem.
"""
import pytest
from datetime import datetime, timedelta
from app.api.models import TaskItem, ApiResponse, CookieItem, ProjectItem, TokenItem


class TestTaskItem:
    """Test TaskItem serialization and defaults."""

    def test_defaults(self):
        task = TaskItem(id="t1", stt=1)
        assert task.status == "pending"
        assert task.images_per_prompt == 1
        assert task.quality == "1K"
        assert task.aspect_ratio == "VIDEO_ASPECT_RATIO_LANDSCAPE"
        assert task.error_message == ""
        assert task.reference_images == []

    def test_to_dict(self):
        task = TaskItem(id="t1", stt=1, prompt="hello", quality="4K")
        d = task.to_dict()
        assert d["id"] == "t1"
        assert d["prompt"] == "hello"
        assert d["quality"] == "4K"
        assert "created_at" in d

    def test_from_dict(self):
        data = {
            "id": "t1", "stt": 1, "prompt": "hi",
            "status": "completed", "quality": "2K",
            "images_per_prompt": 3,
        }
        task = TaskItem.from_dict(data)
        assert task.id == "t1"
        assert task.status == "completed"
        assert task.quality == "2K"

    def test_from_dict_with_iso_timestamp(self):
        ts = "2025-01-15T10:30:00"
        task = TaskItem.from_dict({"id": "t1", "stt": 1, "created_at": ts})
        assert task.created_at.year == 2025
        assert task.created_at.month == 1

    def test_from_dict_with_invalid_timestamp(self):
        task = TaskItem.from_dict({"id": "t1", "stt": 1, "created_at": "not-a-date"})
        assert isinstance(task.created_at, datetime)

    def test_from_dict_defaults(self):
        task = TaskItem.from_dict({})
        assert task.id == ""
        assert task.stt == 0
        assert task.status == "pending"

    def test_roundtrip(self):
        original = TaskItem(id="r1", stt=5, prompt="test", quality="4K", status="running")
        restored = TaskItem.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.prompt == original.prompt
        assert restored.quality == original.quality
        assert restored.status == original.status

    def test_reference_images_by_cat_default(self):
        task = TaskItem(id="t1", stt=1)
        assert task.reference_images_by_cat == {"title": [], "scene": [], "style": []}


class TestApiResponse:
    """Test ApiResponse dataclass."""

    def test_success_response(self):
        resp = ApiResponse(success=True, data=[1, 2, 3], message="OK", total=3)
        assert resp.success
        assert resp.total == 3

    def test_error_response(self):
        resp = ApiResponse(success=False, message="Not found")
        assert not resp.success
        assert resp.data is None


class TestCookieItem:
    """Test CookieItem serialization and expiry."""

    def test_defaults(self):
        c = CookieItem(id="c1")
        assert c.status == "unknown"
        assert c.expires_at is None
        assert not c.is_expired

    def test_is_expired_false_when_future(self):
        c = CookieItem(id="c1", expires_at=datetime.now() + timedelta(days=1))
        assert not c.is_expired

    def test_is_expired_true_when_past(self):
        c = CookieItem(id="c1", expires_at=datetime.now() - timedelta(days=1))
        assert c.is_expired

    def test_to_dict(self):
        c = CookieItem(id="c1", name="session", value="abc", domain=".example.com")
        d = c.to_dict()
        assert d["name"] == "session"
        assert d["domain"] == ".example.com"

    def test_from_dict(self):
        data = {"id": "c1", "name": "sid", "value": "v1", "status": "valid"}
        c = CookieItem.from_dict(data)
        assert c.name == "sid"
        assert c.status == "valid"

    def test_from_dict_with_expires_at(self):
        data = {"id": "c1", "expires_at": "2025-12-31T23:59:59"}
        c = CookieItem.from_dict(data)
        assert c.expires_at is not None
        assert c.expires_at.year == 2025

    def test_from_dict_invalid_expires(self):
        data = {"id": "c1", "expires_at": "not-a-date"}
        c = CookieItem.from_dict(data)
        assert c.expires_at is None


class TestProjectItem:
    """Test ProjectItem serialization."""

    def test_defaults(self):
        p = ProjectItem(id="p1")
        assert p.status == "active"
        assert p.name == ""

    def test_to_dict(self):
        p = ProjectItem(id="p1", name="My Project", description="desc")
        d = p.to_dict()
        assert d["name"] == "My Project"
        assert "created_at" in d

    def test_from_dict(self):
        data = {"id": "p1", "name": "proj", "status": "archived"}
        p = ProjectItem.from_dict(data)
        assert p.name == "proj"
        assert p.status == "archived"

    def test_roundtrip(self):
        original = ProjectItem(id="p1", name="Proj", description="A project")
        restored = ProjectItem.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.name == original.name


class TestTokenItem:
    """Test TokenItem serialization and expiry."""

    def test_defaults(self):
        t = TokenItem(id="t1")
        assert t.token_type == "bearer"
        assert t.status == "active"
        assert not t.is_expired

    def test_is_expired_past(self):
        t = TokenItem(id="t1", expires_at=datetime.now() - timedelta(hours=1))
        assert t.is_expired

    def test_is_expired_future(self):
        t = TokenItem(id="t1", expires_at=datetime.now() + timedelta(hours=1))
        assert not t.is_expired

    def test_to_dict(self):
        t = TokenItem(id="t1", name="key", value="secret", token_type="api_key")
        d = t.to_dict()
        assert d["token_type"] == "api_key"

    def test_from_dict(self):
        data = {"id": "t1", "name": "k", "value": "s", "status": "revoked"}
        t = TokenItem.from_dict(data)
        assert t.status == "revoked"

    def test_roundtrip(self):
        original = TokenItem(id="t1", name="token", value="val")
        restored = TokenItem.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.value == original.value

    def test_from_dict_with_expires(self):
        data = {"id": "t1", "expires_at": "2025-06-01T00:00:00"}
        t = TokenItem.from_dict(data)
        assert t.expires_at is not None

    def test_from_dict_invalid_expires(self):
        data = {"id": "t1", "expires_at": "bad-date"}
        t = TokenItem.from_dict(data)
        assert t.expires_at is None
