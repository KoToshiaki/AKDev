# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests: toolbar button composition after v0.2 simplification."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from PySide6.QtGui import QKeySequence
from ui.win import MainWin


def _toolbar_action_texts(win: MainWin) -> list[str]:
    return [a.text() for a in win._toolbar.actions() if not a.isSeparator()]


def test_toolbar_ref_exists():
    assert hasattr(MainWin(), "_toolbar")


def test_toolbar_excludes_new_project():
    assert "New Project" not in _toolbar_action_texts(MainWin())


def test_toolbar_excludes_pause():
    assert "Pause" not in _toolbar_action_texts(MainWin())


def test_new_project_action_exists_but_not_in_toolbar():
    """New Project action is accessible on the window but not placed in the toolbar."""
    win = MainWin()
    assert hasattr(win, "_a_new")
    assert win._a_new.text() == "New Project"
    assert "New Project" not in _toolbar_action_texts(win)


def test_pause_action_exists_but_not_in_toolbar():
    """Pause action is accessible on the window but not placed in the toolbar."""
    win = MainWin()
    assert hasattr(win, "_a_pause")
    assert win._a_pause.text() == "Pause"
    assert "Pause" not in _toolbar_action_texts(win)


def test_shortcuts_intact():
    win = MainWin()
    assert win._a_build.shortcut() == QKeySequence("F5")
    assert win._a_run.shortcut()   == QKeySequence("Ctrl+R")
    assert win._a_step.shortcut()  == QKeySequence("F10")
    assert win._a_reset.shortcut() == QKeySequence("Ctrl+Shift+R")
    assert win._a_pause.shortcut() == QKeySequence("F6")
