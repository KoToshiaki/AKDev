# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for New Project / Open Project / Save Project / Save Project As dialogs."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_win() -> MainWin:
    win = MainWin()
    assert win._project_root is None
    return win


# ---------------------------------------------------------------------------
# New Project
# ---------------------------------------------------------------------------

def test_new_project_creates_structure(tmp_path):
    win = _make_win()
    proj_dir = tmp_path / "MyProject"
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(tmp_path)), \
         patch("ui.win.QInputDialog.getText", return_value=("MyProject", True)):
        win._new_project()
    assert win._project_root == proj_dir
    assert (proj_dir / "project.json").exists()
    assert (proj_dir / "system.json").exists()
    assert (proj_dir / "src").is_dir()
    assert (proj_dir / "build" / "out").is_dir()
    assert (proj_dir / "asset").is_dir()


def test_new_project_clears_canvas(tmp_path):
    win = _make_win()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(tmp_path)), \
         patch("ui.win.QInputDialog.getText", return_value=("P", True)):
        win._new_project()
    assert win._canvas.export_parts() == []


def test_new_project_cancel_folder_leaves_root_unchanged(tmp_path):
    win = _make_win()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=""), \
         patch("ui.win.QInputDialog.getText", return_value=("P", True)):
        win._new_project()
    assert win._project_root is None


def test_new_project_cancel_name_leaves_root_unchanged(tmp_path):
    win = _make_win()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(tmp_path)), \
         patch("ui.win.QInputDialog.getText", return_value=("", False)):
        win._new_project()
    assert win._project_root is None


def test_new_project_existing_folder_aborts(tmp_path):
    win = _make_win()
    existing = tmp_path / "Exists"
    existing.mkdir()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(tmp_path)), \
         patch("ui.win.QInputDialog.getText", return_value=("Exists", True)):
        win._new_project()
    assert win._project_root is None
    log = win._log.toPlainText()
    assert "既に存在します" in log


# ---------------------------------------------------------------------------
# Open Project
# ---------------------------------------------------------------------------

def test_open_project_sets_root(tmp_path):
    from core.project import create_project
    proj = tmp_path / "TestProj"
    create_project(proj, "TestProj")
    win = _make_win()
    proj_json = str(proj / "project.json")
    with patch("ui.win.QFileDialog.getOpenFileName", return_value=(proj_json, "")):
        win._open_project()
    assert win._project_root == proj


def test_open_project_cancel_leaves_root_unchanged():
    win = _make_win()
    with patch("ui.win.QFileDialog.getOpenFileName", return_value=("", "")):
        win._open_project()
    assert win._project_root is None


def test_open_project_bad_json_logs_error(tmp_path):
    bad = tmp_path / "project.json"
    bad.write_text("NOT JSON", encoding="utf-8")
    win = _make_win()
    with patch("ui.win.QFileDialog.getOpenFileName", return_value=(str(bad), "")):
        win._open_project()
    assert win._project_root is None
    assert "Open failed" in win._log.toPlainText()


# ---------------------------------------------------------------------------
# Save Project
# ---------------------------------------------------------------------------

def test_save_project_no_root_logs_guidance():
    win = _make_win()
    win._save_project()
    log = win._log.toPlainText()
    assert "Save:" in log
    assert "先に行ってください" in log


def test_save_project_writes_system_json(tmp_path):
    from core.project import create_project, load_project
    proj = tmp_path / "SaveTest"
    create_project(proj, "SaveTest")
    win = _make_win()
    win._project_root = proj
    win._editor_tabs.set_project_root(proj)
    win._save_project()
    _, system = load_project(proj)
    assert "parts" in system


# ---------------------------------------------------------------------------
# Save Project As
# ---------------------------------------------------------------------------

def test_save_as_creates_new_project(tmp_path):
    from core.project import create_project
    src = tmp_path / "Src"
    create_project(src, "Src")
    win = _make_win()
    win._project_root = src
    win._editor_tabs.set_project_root(src)

    dest_parent = tmp_path / "dest"
    dest_parent.mkdir()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(dest_parent)), \
         patch("ui.win.QInputDialog.getText", return_value=("NewProj", True)):
        win._save_project_as()

    new_root = dest_parent / "NewProj"
    assert win._project_root == new_root
    assert (new_root / "project.json").exists()
    assert (new_root / "system.json").exists()


def test_save_as_switches_subsequent_save(tmp_path):
    from core.project import create_project, load_project
    src = tmp_path / "Src"
    create_project(src, "Src")
    win = _make_win()
    win._project_root = src
    win._editor_tabs.set_project_root(src)

    dest_parent = tmp_path / "dest"
    dest_parent.mkdir()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(dest_parent)), \
         patch("ui.win.QInputDialog.getText", return_value=("NewProj", True)):
        win._save_project_as()

    new_root = dest_parent / "NewProj"
    win._save_project()
    _, system = load_project(new_root)
    assert "parts" in system


def test_save_as_cancel_folder_leaves_root_unchanged(tmp_path):
    from core.project import create_project
    src = tmp_path / "Src"
    create_project(src, "Src")
    win = _make_win()
    win._project_root = src
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=""), \
         patch("ui.win.QInputDialog.getText", return_value=("N", True)):
        win._save_project_as()
    assert win._project_root == src


def test_save_as_cancel_name_leaves_root_unchanged(tmp_path):
    from core.project import create_project
    src = tmp_path / "Src"
    create_project(src, "Src")
    win = _make_win()
    win._project_root = src
    dest_parent = tmp_path / "dest"
    dest_parent.mkdir()
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(dest_parent)), \
         patch("ui.win.QInputDialog.getText", return_value=("", False)):
        win._save_project_as()
    assert win._project_root == src


def test_save_as_existing_folder_aborts(tmp_path):
    from core.project import create_project
    src = tmp_path / "Src"
    create_project(src, "Src")
    existing = tmp_path / "Existing"
    existing.mkdir()
    win = _make_win()
    win._project_root = src
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(tmp_path)), \
         patch("ui.win.QInputDialog.getText", return_value=("Existing", True)):
        win._save_project_as()
    assert win._project_root == src
    assert "既に存在します" in win._log.toPlainText()
