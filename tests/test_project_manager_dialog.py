"""
Tests for ProjectManagerDialog — project CRUD dialog.
"""
import pytest
from unittest.mock import MagicMock
from app.widgets.project_manager_dialog import ProjectManagerDialog


@pytest.fixture
def flow_api():
    api = MagicMock()
    api.get_flows.return_value = MagicMock(
        success=True,
        data={
            "items": [
                {"id": 1, "name": "Project A", "status": "active",
                 "updated_at": "2026-01-01T12:00:00"},
                {"id": 2, "name": "Project B", "status": "pending",
                 "updated_at": "2026-01-02T12:00:00"},
            ]
        }
    )
    api.create_flow.return_value = MagicMock(success=True, data={"id": 3, "name": "New"})
    api.update_flow.return_value = MagicMock(success=True)
    api.delete_flow.return_value = MagicMock(success=True)
    return api


class TestProjectManagerDialogInit:
    """Test dialog construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, flow_api):
        self.dialog = ProjectManagerDialog(
            mock_api, translator, flow_api=flow_api
        )
        qtbot.addWidget(self.dialog)

    def test_window_title(self):
        assert self.dialog.windowTitle()

    def test_minimum_size(self):
        assert self.dialog.minimumWidth() >= 750
        assert self.dialog.minimumHeight() >= 520

    def test_modal(self):
        assert self.dialog.isModal()

    def test_has_table(self):
        assert self.dialog._table is not None

    def test_has_name_input(self):
        assert self.dialog._name_input is not None

    def test_has_save_btn(self):
        assert self.dialog._save_btn is not None

    def test_has_close_btn(self):
        assert self.dialog._close_btn is not None

    def test_has_cookie_btn(self):
        assert self.dialog._cookie_btn is not None

    def test_table_loads_projects(self):
        assert self.dialog._table.rowCount() >= 2


class TestProjectManagerDialogSave:
    """Test create/update flow."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, flow_api):
        self.flow_api = flow_api
        self.dialog = ProjectManagerDialog(
            mock_api, translator, flow_api=flow_api
        )
        qtbot.addWidget(self.dialog)

    def test_save_new_project(self):
        self.dialog._name_input.setText("New Project")
        self.dialog._on_save()
        self.flow_api.create_flow.assert_called_once()

    def test_save_empty_name_does_nothing(self):
        self.dialog._name_input.setText("")
        self.dialog._on_save()
        self.flow_api.create_flow.assert_not_called()


class TestProjectManagerDialogEdit:
    """Test edit mode."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, flow_api):
        self.dialog = ProjectManagerDialog(
            mock_api, translator, flow_api=flow_api
        )
        qtbot.addWidget(self.dialog)

    def test_on_edit_populates_form(self):
        proj = {"name": "Existing"}
        self.dialog._on_edit("1", proj)
        assert self.dialog._name_input.text() == "Existing"
        assert self.dialog._editing_id == "1"

    def test_cancel_edit_clears_form(self):
        self.dialog._on_edit("1", {"name": "X"})
        self.dialog._on_cancel_edit()
        assert self.dialog._editing_id is None
        assert self.dialog._name_input.text() == ""


class TestProjectManagerDialogSignals:
    """Test signal emission."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, flow_api):
        self.dialog = ProjectManagerDialog(
            mock_api, translator, flow_api=flow_api
        )
        self.qtbot = qtbot
        qtbot.addWidget(self.dialog)

    def test_activate_emits_signals(self):
        with self.qtbot.waitSignal(self.dialog.project_activated, timeout=500):
            self.dialog._on_activate("1", "Project A")

    def test_activate_with_id_emits(self):
        with self.qtbot.waitSignal(self.dialog.project_activated_with_id, timeout=500):
            self.dialog._on_activate("1", "Project A")
