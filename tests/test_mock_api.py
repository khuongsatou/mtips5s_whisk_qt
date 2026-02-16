"""
Tests for MockApi — queue CRUD, execution, cookie, project, and token management.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch
from app.api.mock_api import MockApi
from app.api.models import ApiResponse, TaskItem


def _seed_tasks(api, count=3):
    """Helper to add sample tasks to the queue."""
    ids = []
    for i in range(count):
        resp = api.add_to_queue({
            "prompt": f"Prompt {i + 1}",
            "model": "Nano Banana Pro",
            "aspect_ratio": "16:9",
        })
        ids.append(resp.data["id"])
    return ids


class TestMockApiQueue:
    """Test queue CRUD operations."""

    def test_initial_queue_empty(self, mock_api):
        response = mock_api.get_queue()
        assert response.success is True
        assert len(response.data) == 0
        assert response.total == 0

    def test_get_task_by_id(self, mock_api):
        _seed_tasks(mock_api, 1)
        all_tasks = mock_api.get_queue()
        first_id = all_tasks.data[0]["id"]
        response = mock_api.get_task(first_id)
        assert response.success is True
        assert response.data["id"] == first_id

    def test_get_nonexistent_task(self, mock_api):
        response = mock_api.get_task("nonexistent-uuid")
        assert response.success is False

    def test_add_to_queue(self, mock_api):
        response = mock_api.add_to_queue({
            "prompt": "A beautiful sunset",
            "model": "Nano Banana Pro",
            "aspect_ratio": "16:9",
        })
        assert response.success is True
        assert response.data["prompt"] == "A beautiful sunset"
        assert response.data["status"] == "pending"
        after = mock_api.get_queue()
        assert len(after.data) == 1

    def test_add_to_queue_auto_stt(self, mock_api):
        response = mock_api.add_to_queue({"prompt": "test"})
        assert response.data["stt"] == 1
        response2 = mock_api.add_to_queue({"prompt": "test2"})
        assert response2.data["stt"] == 2

    def test_update_task(self, mock_api):
        _seed_tasks(mock_api, 1)
        all_tasks = mock_api.get_queue()
        first_id = all_tasks.data[0]["id"]
        response = mock_api.update_task(first_id, {
            "prompt": "Updated prompt",
            "status": "error",
            "error_message": "API timeout",
        })
        assert response.success is True
        assert response.data["prompt"] == "Updated prompt"
        assert response.data["status"] == "error"

    def test_update_nonexistent_task(self, mock_api):
        resp = mock_api.update_task("bad-id", {"prompt": "x"})
        assert resp.success is False

    def test_delete_tasks(self, mock_api):
        ids = _seed_tasks(mock_api, 3)
        response = mock_api.delete_tasks([ids[0]])
        assert response.success is True
        after = mock_api.get_queue()
        assert len(after.data) == 2
        assert after.data[0]["stt"] == 1

    def test_clear_queue(self, mock_api):
        _seed_tasks(mock_api, 3)
        response = mock_api.clear_queue()
        assert response.success is True
        after = mock_api.get_queue()
        assert len(after.data) == 0

    def test_task_data_structure(self, mock_api):
        _seed_tasks(mock_api, 1)
        response = mock_api.get_queue()
        task = response.data[0]
        required_fields = [
            "id", "stt", "task_name", "model", "aspect_ratio",
            "prompt", "status", "elapsed_seconds", "created_at",
        ]
        for field in required_fields:
            assert field in task, f"Missing field: {field}"


class TestMockApiExecution:
    """Test queue execution: run_selected, run_all, pause, stop, retry."""

    def test_run_selected_marks_pending_as_running(self, mock_api):
        ids = _seed_tasks(mock_api, 2)
        resp = mock_api.run_selected([ids[0]])
        assert resp.success is True
        task = mock_api.get_task(ids[0])
        assert task.data["status"] == "running"
        # Second task still pending
        task2 = mock_api.get_task(ids[1])
        assert task2.data["status"] == "pending"

    def test_run_selected_skips_non_pending(self, mock_api):
        ids = _seed_tasks(mock_api, 1)
        mock_api.update_task(ids[0], {"status": "completed"})
        resp = mock_api.run_selected(ids)
        assert "0" in resp.message  # 0 started

    def test_run_all_marks_all_pending(self, mock_api):
        ids = _seed_tasks(mock_api, 3)
        resp = mock_api.run_all()
        assert resp.success is True
        for task_id in ids:
            task = mock_api.get_task(task_id)
            assert task.data["status"] == "running"

    def test_pause(self, mock_api):
        resp = mock_api.pause()
        assert resp.success is True
        assert mock_api._is_paused is True

    def test_stop_resets_running_to_pending(self, mock_api):
        ids = _seed_tasks(mock_api, 2)
        mock_api.run_all()
        resp = mock_api.stop()
        assert resp.success is True
        for task_id in ids:
            task = mock_api.get_task(task_id)
            assert task.data["status"] == "pending"
        assert mock_api._is_running is False

    def test_retry_errors(self, mock_api):
        ids = _seed_tasks(mock_api, 1)
        mock_api.update_task(ids[0], {"status": "error", "error_message": "fail"})
        resp = mock_api.retry_errors()
        assert resp.success is True
        task = mock_api.get_task(ids[0])
        assert task.data["status"] == "pending"
        assert task.data["error_message"] == ""


class TestMockApiCookies:
    """Test cookie management CRUD."""

    def test_get_cookies(self, mock_api):
        resp = mock_api.get_cookies()
        assert resp.success is True
        assert isinstance(resp.data, list)

    def test_add_cookie(self, mock_api):
        resp = mock_api.add_cookie({
            "name": "Test Cookie", "value": "abc123", "domain": "example.com",
        })
        assert resp.success is True
        assert resp.data["name"] == "Test Cookie"
        assert resp.data["status"] == "unknown"

    def test_delete_cookie(self, mock_api):
        add_resp = mock_api.add_cookie({"name": "Del Me", "value": "x", "domain": "x"})
        cookie_id = add_resp.data["id"]
        del_resp = mock_api.delete_cookie(cookie_id)
        assert del_resp.success is True

    def test_delete_nonexistent_cookie(self, mock_api):
        resp = mock_api.delete_cookie("bad-id")
        assert resp.success is False

    def test_refresh_cookies(self, mock_api):
        mock_api.add_cookie({"name": "c1", "value": "v1", "domain": "d"})
        resp = mock_api.refresh_cookies()
        assert resp.success is True
        assert len(resp.data) >= 1

    def test_check_cookie(self, mock_api):
        add_resp = mock_api.add_cookie({"name": "check", "value": "v", "domain": "d"})
        cookie_id = add_resp.data["id"]
        resp = mock_api.check_cookie(cookie_id)
        assert resp.success is True

    def test_check_nonexistent_cookie(self, mock_api):
        resp = mock_api.check_cookie("bad-id")
        assert resp.success is False


class TestMockApiProjects:
    """Test project management CRUD."""

    def test_get_projects(self, mock_api):
        resp = mock_api.get_projects()
        assert resp.success is True

    def test_add_project(self, mock_api):
        resp = mock_api.add_project({"name": "My Project", "description": "Test"})
        assert resp.success is True
        assert resp.data["name"] == "My Project"
        assert resp.data["status"] == "active"

    def test_update_project(self, mock_api):
        add_resp = mock_api.add_project({"name": "Proj", "description": "d"})
        pid = add_resp.data["id"]
        upd_resp = mock_api.update_project(pid, {"name": "Updated"})
        assert upd_resp.success is True
        assert upd_resp.data["name"] == "Updated"

    def test_update_nonexistent_project(self, mock_api):
        resp = mock_api.update_project("bad", {"name": "x"})
        assert resp.success is False

    def test_delete_project(self, mock_api):
        add_resp = mock_api.add_project({"name": "Del", "description": "d"})
        pid = add_resp.data["id"]
        del_resp = mock_api.delete_project(pid)
        assert del_resp.success is True

    def test_delete_nonexistent_project(self, mock_api):
        resp = mock_api.delete_project("bad-id")
        assert resp.success is False

    def test_set_active_project(self, mock_api):
        add_resp = mock_api.add_project({"name": "Active", "description": ""})
        pid = add_resp.data["id"]
        resp = mock_api.set_active_project(pid)
        assert resp.success is True

    def test_set_active_nonexistent(self, mock_api):
        resp = mock_api.set_active_project("bad")
        assert resp.success is False

    def test_get_active_project(self, mock_api):
        add_resp = mock_api.add_project({"name": "Act", "description": ""})
        pid = add_resp.data["id"]
        mock_api.set_active_project(pid)
        resp = mock_api.get_active_project()
        assert resp.success is True
        assert resp.data["id"] == pid

    def test_get_active_project_none_set(self, mock_api):
        resp = mock_api.get_active_project()
        assert resp.success is True


class TestMockApiTokens:
    """Test token management CRUD."""

    def test_get_tokens(self, mock_api):
        resp = mock_api.get_tokens()
        assert resp.success is True

    def test_add_token(self, mock_api):
        resp = mock_api.add_token({
            "name": "API Key", "value": "sk-123", "token_type": "api_key",
        })
        assert resp.success is True
        assert resp.data["name"] == "API Key"
        assert resp.data["status"] == "active"

    def test_add_token_with_expiry_days(self, mock_api):
        resp = mock_api.add_token({
            "name": "t", "value": "v", "expires_at": 30,
        })
        assert resp.success is True
        assert resp.data["expires_at"] is not None

    def test_add_token_with_expiry_iso(self, mock_api):
        resp = mock_api.add_token({
            "name": "t", "value": "v", "expires_at": "2030-12-31",
        })
        assert resp.success is True

    def test_add_token_with_invalid_expiry_string(self, mock_api):
        resp = mock_api.add_token({
            "name": "t", "value": "v", "expires_at": "not-a-date",
        })
        assert resp.success is True  # Graceful fallback to None

    def test_update_token(self, mock_api):
        add_resp = mock_api.add_token({"name": "old", "value": "v"})
        tid = add_resp.data["id"]
        upd_resp = mock_api.update_token(tid, {"name": "new"})
        assert upd_resp.success is True
        assert upd_resp.data["name"] == "new"

    def test_update_token_expiry_days(self, mock_api):
        add_resp = mock_api.add_token({"name": "t", "value": "v"})
        tid = add_resp.data["id"]
        upd_resp = mock_api.update_token(tid, {"expires_at": 7})
        assert upd_resp.success is True

    def test_update_token_expiry_iso(self, mock_api):
        add_resp = mock_api.add_token({"name": "t", "value": "v"})
        tid = add_resp.data["id"]
        upd_resp = mock_api.update_token(tid, {"expires_at": "2030-06-15"})
        assert upd_resp.success is True

    def test_update_token_expiry_invalid(self, mock_api):
        add_resp = mock_api.add_token({"name": "t", "value": "v"})
        tid = add_resp.data["id"]
        upd_resp = mock_api.update_token(tid, {"expires_at": "bad"})
        assert upd_resp.success is True  # Graceful fallback

    def test_update_token_expiry_none(self, mock_api):
        add_resp = mock_api.add_token({"name": "t", "value": "v"})
        tid = add_resp.data["id"]
        upd_resp = mock_api.update_token(tid, {"expires_at": None})
        assert upd_resp.success is True

    def test_update_nonexistent_token(self, mock_api):
        resp = mock_api.update_token("bad", {"name": "x"})
        assert resp.success is False

    def test_delete_token(self, mock_api):
        add_resp = mock_api.add_token({"name": "del", "value": "v"})
        tid = add_resp.data["id"]
        del_resp = mock_api.delete_token(tid)
        assert del_resp.success is True

    def test_delete_nonexistent_token(self, mock_api):
        resp = mock_api.delete_token("bad-id")
        assert resp.success is False


class TestMockApiCheckpoint:
    """Test checkpoint save/load/clear."""

    def test_clear_checkpoint(self, mock_api):
        _seed_tasks(mock_api, 2)
        resp = mock_api.clear_checkpoint()
        assert resp.success is True
        q = mock_api.get_queue()
        assert len(q.data) == 0
