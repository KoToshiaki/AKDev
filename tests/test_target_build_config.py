# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for target.json build config loading and Build pipeline dispatch."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

import pytest

from core.project import (
    create_project,
    default_target_config,
    load_target,
    load_tools,
    src_type,
)
from ui.win import MainWin


# ---------------------------------------------------------------------------
# load_target() tests
# ---------------------------------------------------------------------------

def test_load_target_reads_existing_file(tmp_path):
    proj = create_project(tmp_path / "p", "p")
    result = load_target(proj)
    assert result["target"]["name"] == "AK32 Baremetal"
    assert result["build"]["type"] == "internal_assembler"


def test_load_target_returns_default_when_missing(tmp_path):
    result = load_target(tmp_path)  # no target.json in tmp_path
    assert result == default_target_config()


def test_load_target_custom_file(tmp_path):
    custom = {
        "target": {"name": "Custom"},
        "build": {"type": "external_command", "command": "make"},
    }
    (tmp_path / "target.json").write_text(json.dumps(custom), encoding="utf-8")
    result = load_target(tmp_path)
    assert result["build"]["type"] == "external_command"


def test_load_target_corrupt_json_raises(tmp_path):
    (tmp_path / "target.json").write_text("{bad json", encoding="utf-8")
    with pytest.raises(Exception):
        load_target(tmp_path)


# ---------------------------------------------------------------------------
# load_tools() tests
# ---------------------------------------------------------------------------

def test_load_tools_reads_existing_file(tmp_path):
    proj = create_project(tmp_path / "p", "p")
    result = load_tools(proj)
    assert "vscode" in result["tools"]


def test_load_tools_returns_default_when_missing(tmp_path):
    from core.project import default_tools_config
    result = load_tools(tmp_path)
    assert result == default_tools_config()


# ---------------------------------------------------------------------------
# src_type() tests
# ---------------------------------------------------------------------------

def test_src_type_asm():
    assert src_type("main.asm") == "asm"


def test_src_type_verilog():
    assert src_type("cpu.v") == "hdl"


def test_src_type_vhdl():
    assert src_type("cpu.vhd") == "hdl"


def test_src_type_c():
    assert src_type("main.c") == "c"


def test_src_type_cpp():
    assert src_type("main.cpp") == "cpp"
    assert src_type("main.cc") == "cpp"
    assert src_type("main.cxx") == "cpp"


def test_src_type_linker():
    assert src_type("link.ld") == "linker"


def test_src_type_binary():
    assert src_type("out.bin") == "binary"
    assert src_type("rom.hex") == "binary"


def test_src_type_custom():
    assert src_type("script.ak") == "custom"
    assert src_type("noext") == "custom"


def test_src_type_case_insensitive():
    assert src_type("MAIN.ASM") == "asm"
    assert src_type("CPU.V") == "hdl"


# ---------------------------------------------------------------------------
# Build dispatch tests (via MainWin headless)
# ---------------------------------------------------------------------------

_HI_SRC = """\
LDI r2, 0x100
LDI r1, 72
OUT [r2], r1
LDI r1, 105
OUT [r2], r1
HALT
"""

_FAKE_PART = {"id": "ak32_cpu", "name": "AK32 CPU"}


def _make_win_with_project(tmp_path) -> MainWin:
    win = MainWin()
    proj_dir = tmp_path / "Proj"
    with patch("ui.win.QFileDialog.getExistingDirectory", return_value=str(tmp_path)), \
         patch("ui.win.QInputDialog.getText", return_value=("Proj", True)):
        win._new_project()
    assert win._project_root == proj_dir
    return win


def _log_text(win: MainWin) -> str:
    return win._log.toPlainText()


def test_build_internal_assembler_succeeds(tmp_path):
    """internal_assembler type: build produces .bin and loads into RAM."""
    win = _make_win_with_project(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    win._build()

    log = _log_text(win)
    assert "Build succeeded" in log
    assert "Loaded binary to RAM" in log
    bin_path = win._project_root / "build" / "out" / "hello.bin"
    assert bin_path.exists()


def test_build_no_tab_shows_error(tmp_path):
    win = _make_win_with_project(tmp_path)
    win._build()
    assert "current tab is not an asm file" in _log_text(win)


def test_build_no_project_shows_error(tmp_path):
    win = MainWin()
    # open_tab() requires project_root; set a dummy root to open the tab,
    # then clear MainWin._project_root to simulate "no project open" state.
    win._editor_tabs.set_project_root(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "node_0001", "asm", "hello.asm")
    win._project_root = None
    win._build()
    assert "New Project" in _log_text(win) or "Open Project" in _log_text(win)


def test_build_external_command_not_implemented(tmp_path):
    """external_command type: build logs not-implemented and stops."""
    win = _make_win_with_project(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    # Overwrite target.json with external_command type
    target_path = win._project_root / "target.json"
    target_path.write_text(
        json.dumps({"target": {}, "build": {"type": "external_command"}}),
        encoding="utf-8",
    )

    win._build()

    log = _log_text(win)
    assert "external_command is not implemented yet" in log
    assert "Build succeeded" not in log


def test_build_unsupported_type_shows_error(tmp_path):
    """Unknown build type: logs unsupported and stops."""
    win = _make_win_with_project(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    target_path = win._project_root / "target.json"
    target_path.write_text(
        json.dumps({"target": {}, "build": {"type": "future_compiler"}}),
        encoding="utf-8",
    )

    win._build()

    log = _log_text(win)
    assert "unsupported build type: future_compiler" in log
    assert "Build succeeded" not in log


def test_build_without_target_json_uses_default(tmp_path):
    """No target.json: falls back to internal_assembler default and builds successfully."""
    win = _make_win_with_project(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    # Remove target.json to simulate an old project
    (win._project_root / "target.json").unlink()

    win._build()

    log = _log_text(win)
    assert "Build succeeded" in log


def test_build_asm_error_reported(tmp_path):
    win = _make_win_with_project(tmp_path)
    win._editor_tabs.open_tab(_FAKE_PART, "node_0001", "asm", "bad.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText("NOP\nBAD_INSTR\nHALT")

    win._build()

    assert "Build FAILED" in _log_text(win)
