# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests: Ribbon command bar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from PySide6.QtGui import QKeySequence, QAction
from ui.ribbon import RibbonBar
from ui.win import MainWin


# ---------------------------------------------------------------------------
# RibbonBar standalone
# ---------------------------------------------------------------------------

def test_ribbon_bar_instantiates():
    ribbon = RibbonBar()
    assert ribbon.page_count() == 0


def test_ribbon_bar_add_page():
    a1 = QAction("Foo")
    a2 = QAction("Bar")
    ribbon = RibbonBar()
    ribbon.add_page("Test", [a1, a2])
    assert ribbon.page_count() == 1
    assert ribbon.page_title(0) == "Test"
    assert ribbon.page_action_texts(0) == ["Foo", "Bar"]


def test_ribbon_bar_multiple_pages():
    ribbon = RibbonBar()
    ribbon.add_page("A", [])
    ribbon.add_page("B", [])
    ribbon.add_page("C", [])
    assert ribbon.page_count() == 3
    assert [ribbon.page_title(i) for i in range(3)] == ["A", "B", "C"]


def test_ribbon_bar_default_button_min_size():
    # Patch 2 (B): buttons are compact — natural width (0) + modest min height.
    ribbon = RibbonBar()
    w, h = ribbon.button_min_size()
    assert w == 0          # natural width, not stretched edge-to-edge
    assert 0 < h <= 40


def test_ribbon_bar_custom_button_min_size():
    ribbon = RibbonBar(button_min_width=120, button_min_height=56)
    assert ribbon.button_min_size() == (120, 56)


# ---------------------------------------------------------------------------
# MainWin ribbon integration
# ---------------------------------------------------------------------------

def _titles(win: MainWin) -> list[str]:
    return [win._ribbon.page_title(i) for i in range(win._ribbon.page_count())]


def test_ribbon_ref_exists():
    assert hasattr(MainWin(), "_ribbon")


def test_ribbon_has_five_pages():
    # Patch 2 (A): Project tab removed.
    win = MainWin()
    assert win._ribbon.page_count() == 5


def test_ribbon_page_titles():
    win = MainWin()
    titles = _titles(win)
    for expected in ("Parts", "Wiring", "Run", "View", "Debug"):
        assert expected in titles, f"'{expected}' tab missing from ribbon"


def test_ribbon_no_project_tab():
    # Patch 2 (A): Project tab is gone; File menu keeps the project actions.
    win = MainWin()
    assert "Project" not in _titles(win)


def test_ribbon_parts_page():
    # Patch 2 (C): meaningful operations only.
    win = MainWin()
    idx = _titles(win).index("Parts")
    texts = win._ribbon.page_action_texts(idx)
    for name in ("Parts Library", "Import Part…", "Open Parts Folder"):
        assert name in texts, f"'{name}' missing from Parts tab"
    for gone in ("Add Part", "Clone", "Delete"):
        assert gone not in texts, f"'{gone}' should be removed from Parts tab"


def test_ribbon_wiring_page():
    win = MainWin()
    idx = _titles(win).index("Wiring")
    texts = win._ribbon.page_action_texts(idx)
    for name in ("Wire Mode", "Cancel Wire"):
        assert name in texts, f"'{name}' missing from Wiring tab"


def test_ribbon_run_page():
    win = MainWin()
    idx = _titles(win).index("Run")
    texts = win._ribbon.page_action_texts(idx)
    for name in ("Build", "Reset", "Run", "Step", "Pause"):
        assert name in texts, f"'{name}' missing from Run tab"


def test_ribbon_view_page():
    # Patch 2 (H): Zoom In/Out removed (wheel zoom remains); Fit/Reset kept.
    win = MainWin()
    idx = _titles(win).index("View")
    texts = win._ribbon.page_action_texts(idx)
    for name in ("Grid", "Snap", "Reset Zoom", "Fit", "Properties"):
        assert name in texts, f"'{name}' missing from View tab"
    for gone in ("Zoom In", "Zoom Out"):
        assert gone not in texts, f"'{gone}' should be removed from View tab"


def test_ribbon_debug_page():
    # Patch 2 (I): Log and Console are separate entries.
    win = MainWin()
    idx = _titles(win).index("Debug")
    texts = win._ribbon.page_action_texts(idx)
    for name in ("Register View", "Memory", "Bus Trace",
                 "UART Console", "Log", "Console"):
        assert name in texts, f"'{name}' missing from Debug tab"


def test_ribbon_button_min_size():
    # Patch 2 (B): compact buttons — natural width, modest height.
    win = MainWin()
    w, h = win._ribbon.button_min_size()
    assert w == 0
    assert 0 < h <= 40


def test_menubar_has_only_file():
    win = MainWin()
    menu_titles = [a.text() for a in win.menuBar().actions()]
    assert menu_titles == ["File"], f"Expected ['File'] only, got {menu_titles}"


def test_ribbon_shortcuts_intact():
    win = MainWin()
    assert win._a_new.shortcut()   == QKeySequence("Ctrl+N")
    assert win._a_open.shortcut()  == QKeySequence("Ctrl+O")
    assert win._a_save.shortcut()  == QKeySequence("Ctrl+S")
    assert win._a_build.shortcut() == QKeySequence("F5")
    assert win._a_run.shortcut()   == QKeySequence("Ctrl+R")
    assert win._a_step.shortcut()  == QKeySequence("F10")
    assert win._a_reset.shortcut() == QKeySequence("Ctrl+Shift+R")
    assert win._a_pause.shortcut() == QKeySequence("F6")
