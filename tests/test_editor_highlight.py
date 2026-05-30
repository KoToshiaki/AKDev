# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for EditorTabs PC-line highlight and MainWin address_map integration."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from ui.editor import EditorTabs  # noqa: E402

_FAKE_PART = {"id": "ak32_cpu", "name": "AK32 CPU"}
_SIMPLE_SRC = "LDI r1, 72\nHALT\n"


# ---------------------------------------------------------------------------
# EditorTabs.highlight_line / clear_highlight — no tabs
# ---------------------------------------------------------------------------

def test_highlight_line_no_tabs_no_crash():
    """highlight_line() with no open tabs does not raise."""
    tabs = EditorTabs()
    tabs.highlight_line(0)


def test_clear_highlight_no_tabs_no_crash():
    """clear_highlight() with no open tabs does not raise."""
    tabs = EditorTabs()
    tabs.clear_highlight()


# ---------------------------------------------------------------------------
# EditorTabs.highlight_line / clear_highlight — with open tab
# ---------------------------------------------------------------------------

def test_highlight_line_with_open_tab(tmp_path):
    """highlight_line(0) with an open tab does not raise."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    tabs.highlight_line(0)


def test_highlight_line_out_of_range(tmp_path):
    """highlight_line() with an out-of-range line_no does not raise."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_SIMPLE_SRC)
    tabs.highlight_line(9999)   # far beyond last line


def test_highlight_line_negative_no_crash(tmp_path):
    """highlight_line() with a negative line_no does not raise."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    tabs.highlight_line(-1)


def test_clear_highlight_after_highlight(tmp_path):
    """clear_highlight() after highlight_line() does not raise."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_SIMPLE_SRC)
    tabs.highlight_line(0)
    tabs.highlight_line(1)
    tabs.clear_highlight()


def test_highlight_multiple_calls_no_crash(tmp_path):
    """Repeated highlight_line() and clear_highlight() calls do not raise."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    for line in range(5):
        tabs.highlight_line(line)
    tabs.clear_highlight()
    tabs.clear_highlight()   # double-clear is safe


def test_highlight_line_after_close_tab(tmp_path):
    """highlight_line() after closing the only tab does not raise."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    tabs.highlight_line(0)
    tabs._close_tab(0)       # close the tab
    tabs.highlight_line(0)   # must not raise with no active tab


# ---------------------------------------------------------------------------
# MainWin address_map integration
# ---------------------------------------------------------------------------

def test_mainwin_address_map_initialized_empty():
    """MainWin._address_map is an empty dict on construction."""
    from ui.win import MainWin
    win = MainWin()
    assert hasattr(win, "_address_map")
    assert isinstance(win._address_map, dict)
    assert len(win._address_map) == 0


def test_mainwin_build_saves_address_map(tmp_path):
    """After a successful Build, _address_map is populated."""
    from ui.win import MainWin
    from PySide6.QtWidgets import QTextEdit
    win = MainWin()
    win._project_root = tmp_path
    win._editor_tabs.set_project_root(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_SIMPLE_SRC)
    win._build()
    assert len(win._address_map) > 0
    assert 0 in win._address_map          # first instruction at byte 0


def test_mainwin_build_fail_clears_address_map(tmp_path):
    """After a failed Build, _address_map is empty."""
    from ui.win import MainWin
    from PySide6.QtWidgets import QTextEdit
    win = MainWin()
    win._address_map = {0: 0, 4: 1}   # pre-populate
    win._project_root = tmp_path
    win._editor_tabs.set_project_root(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "n1", "asm", "main.asm")
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText("UNKNOWN_OP\nHALT\n")
    win._build()
    assert win._address_map == {}


def test_mainwin_step_with_address_map_no_crash():
    """_do_step() with _address_map populated does not raise."""
    from ui.win import MainWin
    from asm.asm import assemble
    win = MainWin()
    binary = assemble(_SIMPLE_SRC)
    win._sim_ram.reset()
    win._sim_ram.load_bytes(binary)
    win._sim_cpu.reset()
    win._address_map = {0: 0, 4: 1}
    win._do_step()   # must not raise


def test_mainwin_run_with_address_map_no_crash():
    """_do_run() with _address_map populated does not raise."""
    from ui.win import MainWin
    from asm.asm import assemble
    win = MainWin()
    binary = assemble(_SIMPLE_SRC)
    win._sim_ram.reset()
    win._sim_ram.load_bytes(binary)
    win._sim_cpu.reset()
    win._address_map = {0: 0, 4: 1}
    win._do_run()   # must not raise


def test_mainwin_reset_clears_highlight_no_crash():
    """_do_reset() does not raise and clears the editor highlight."""
    from ui.win import MainWin
    win = MainWin()
    win._address_map = {0: 0, 4: 1}
    win._do_reset()   # must not raise
