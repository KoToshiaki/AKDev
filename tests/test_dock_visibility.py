# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests: View menu dock visibility toggles."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin


def _win() -> MainWin:
    return MainWin()


# ---------------------------------------------------------------------------
# Dock instance variable existence
# ---------------------------------------------------------------------------

def test_dock_refs_exist():
    """All six docks are stored as instance variables."""
    win = _win()
    assert hasattr(win, "_parts_lib_dock")
    assert hasattr(win, "_props_dock")
    assert hasattr(win, "_reg_view_dock")
    assert hasattr(win, "_log_dock")
    assert hasattr(win, "_uart_console_dock")
    assert hasattr(win, "_bus_trace_dock")


# ---------------------------------------------------------------------------
# toggleViewAction existence and initial state
# ---------------------------------------------------------------------------

def test_view_actions_are_checkable():
    """toggleViewAction for each dock is checkable."""
    win = _win()
    for dock in (
        win._parts_lib_dock, win._props_dock, win._reg_view_dock,
        win._log_dock, win._uart_console_dock, win._bus_trace_dock,
    ):
        assert dock.toggleViewAction().isCheckable()


def test_view_actions_checked_when_visible():
    """toggleViewAction is checked when the dock is visible.

    Patch 2 (D): Parts Library starts hidden, so it is excluded here and
    covered by the dedicated tests below.
    """
    win = _win()
    win.show()
    _app.processEvents()
    for dock in (
        win._props_dock, win._reg_view_dock,
        win._log_dock, win._uart_console_dock, win._bus_trace_dock,
    ):
        assert dock.toggleViewAction().isChecked(), (
            f"{dock.windowTitle()} toggleViewAction should be checked when visible"
        )
    win.close()


def test_parts_lib_hidden_on_start():
    """Patch 2 (D): Parts Library is hidden at startup (Canvas leads)."""
    win = _win()
    win.show()
    _app.processEvents()
    assert not win._parts_lib_dock.isVisible()
    assert not win._parts_lib_dock.toggleViewAction().isChecked()
    win.close()


def test_parts_lib_toggle_shows():
    """Patch 2 (D): the Parts ribbon toggle can show the Parts Library again."""
    win = _win()
    win.show()
    _app.processEvents()
    action = win._parts_lib_dock.toggleViewAction()
    action.trigger()          # check -> show
    _app.processEvents()
    assert win._parts_lib_dock.isVisible()
    assert action.isChecked()
    win.close()


# ---------------------------------------------------------------------------
# hide / show via toggleViewAction
# ---------------------------------------------------------------------------

def test_hide_dock_via_toggle_action():
    """Triggering toggleViewAction hides an initially-visible dock."""
    win = _win()
    win.show()
    _app.processEvents()
    action = win._props_dock.toggleViewAction()
    assert action.isChecked()
    action.trigger()          # uncheck → hide
    _app.processEvents()
    assert not win._props_dock.isVisible()
    assert not action.isChecked()
    win.close()


def test_show_dock_via_toggle_action():
    """Triggering toggleViewAction again shows the dock."""
    win = _win()
    win.show()
    _app.processEvents()
    action = win._props_dock.toggleViewAction()
    action.trigger()   # hide
    _app.processEvents()
    action.trigger()   # show again
    _app.processEvents()
    assert win._props_dock.isVisible()
    assert action.isChecked()
    win.close()


def test_hide_show_all_docks():
    """Each initially-visible dock can be hidden and shown via its toggleViewAction."""
    win = _win()
    win.show()
    _app.processEvents()
    docks = [
        win._props_dock, win._reg_view_dock,
        win._log_dock, win._uart_console_dock, win._bus_trace_dock,
    ]
    for dock in docks:
        action = dock.toggleViewAction()
        action.trigger()    # hide
        _app.processEvents()
        assert not dock.isVisible(), f"{dock.windowTitle()} should be hidden"
        action.trigger()    # show
        _app.processEvents()
        assert dock.isVisible(), f"{dock.windowTitle()} should be visible"
    win.close()


# ---------------------------------------------------------------------------
# Closing dock via hide() syncs toggleViewAction
# ---------------------------------------------------------------------------

def test_hide_dock_directly_syncs_action():
    """Calling dock.hide() (simulating × close) unchecks the toggleViewAction."""
    win = _win()
    win.show()
    _app.processEvents()
    dock = win._reg_view_dock
    action = dock.toggleViewAction()
    assert action.isChecked()
    dock.hide()
    _app.processEvents()
    assert not action.isChecked()
    win.close()
