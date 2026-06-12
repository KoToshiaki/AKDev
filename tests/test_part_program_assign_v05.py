# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PART_PROGRAM_ASSIGN_V05 — assign program sources to parts + Build/Run."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas
from ui.prop import PropPanel
from ui.win import MainWin
from core.project import create_project

_CPU = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB = {_CPU["id"]: _CPU, _RAM["id"]: _RAM}

_HI_SRC = Path(__file__).parent.parent / "src" / "hello.asm"


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _with_cpu() -> Canvas:
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    return c


# ---------------------------------------------------------------------------
# Canvas source API
# ---------------------------------------------------------------------------

def test_set_node_source_returns_true():
    c = _with_cpu()
    assert c.set_node_source("node_0001", "asm", "src/hello.asm") is True
    assert c.node_source("node_0001", "asm") == "src/hello.asm"


def test_set_node_source_unknown_returns_false():
    c = _with_cpu()
    assert c.set_node_source("node_9999", "asm", "x.asm") is False


def test_clear_node_source_removes_asm():
    c = _with_cpu()
    c.set_node_source("node_0001", "asm", "src/hello.asm")
    assert c.clear_node_source("node_0001", "asm") is True
    assert c.node_source("node_0001", "asm") is None


def test_node_sources_returns_dict():
    c = _with_cpu()
    c.set_node_source("node_0001", "asm", "a.asm")
    s = c.node_sources("node_0001")
    assert s.get("asm") == "a.asm"


def test_node_source_handles_dict_form():
    """Future dict form: node_source extracts the path."""
    c = _with_cpu()
    c.get_node("node_0001").set_source("asm", {"path": "src/main.asm", "entry": "main"})
    assert c.node_source("node_0001", "asm") == "src/main.asm"


def test_default_sources_unchanged():
    c = _with_cpu()
    assert c.node_sources("node_0001") == {"asm": None, "hdl": None}


# ---------------------------------------------------------------------------
# resolve priority
# ---------------------------------------------------------------------------

def test_resolve_prefers_selected_node():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    c.set_node_source("node_0001", "asm", "cpu.asm")
    c.set_node_source("node_0002", "asm", "ram.asm")
    c.get_node("node_0002").setSelected(True)
    assert c.resolve_program_source("asm") == "ram.asm"


def test_resolve_prefers_cpu_when_no_selection():
    c = _canvas()
    c.add_part_at(_RAM, QPointF(0.0, 0.0))
    c.add_part_at(_CPU, QPointF(200.0, 0.0))
    c.set_node_source("node_0001", "asm", "ram.asm")
    c.set_node_source("node_0002", "asm", "cpu.asm")
    assert c.resolve_program_source("asm") == "cpu.asm"


def test_resolve_none_when_unassigned():
    c = _with_cpu()
    assert c.resolve_program_source("asm") is None


# ---------------------------------------------------------------------------
# export / import
# ---------------------------------------------------------------------------

def test_export_import_roundtrip_sources():
    c = _with_cpu()
    c.set_node_source("node_0001", "asm", "src/hello.asm")
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    assert c2.node_source("node_0001", "asm") == "src/hello.asm"


def test_import_missing_sources_ok():
    c = _canvas()
    c.import_parts([{"node_id": "node_0001", "part_id": _CPU["id"],
                     "name": "AK32", "x": 0, "y": 0}], _LIB)
    assert c.node_sources("node_0001") == {"asm": None, "hdl": None}


# ---------------------------------------------------------------------------
# Properties panel
# ---------------------------------------------------------------------------

def test_program_box_shown_on_node():
    p = PropPanel()
    p.show_part(_CPU, "node_0001", {"asm": "src/hello.asm", "hdl": None})
    assert not p._program_box.isHidden()
    assert p._src_value["asm"].text() == "src/hello.asm"


def test_program_box_hidden_on_wire():
    p = PropPanel()
    p.show_part(_CPU, "node_0001", {"asm": "a.asm"})
    p.show_wire({"id": "conn_0001", "kind": "bus",
                 "from": {"node_id": "n1"}, "to": {"node_id": "n2"}})
    assert p._program_box.isHidden()


def test_source_set_signal_emits():
    p = PropPanel()
    got = []
    p.source_set_requested.connect(lambda nid, st: got.append((nid, st)))
    p.show_part(_CPU, "node_0001", {})
    p._on_source_set("asm")
    assert got == [("node_0001", "asm")]


def test_source_clear_signal_emits():
    p = PropPanel()
    got = []
    p.source_clear_requested.connect(lambda nid, st: got.append((nid, st)))
    p.show_part(_CPU, "node_0001", {})
    p._on_source_clear("asm")
    assert got == [("node_0001", "asm")]


def test_wire_props_still_work():
    p = PropPanel()
    p.show_wire({"id": "conn_0001", "kind": "bus",
                 "from": {"node_id": "n1"}, "to": {"node_id": "n2"}})
    assert not p._wire_box.isHidden()
    assert p._program_box.isHidden()


def test_visual_palette_still_works():
    p = PropPanel()
    p.show_part(_CPU, "node_0001", {})
    assert not p._visual_box.isHidden()
    assert p.palette_size() > 0


# ---------------------------------------------------------------------------
# MainWin: open + build/run with assigned source
# ---------------------------------------------------------------------------

def _make_win_with_project(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def test_open_source_logs_when_unassigned(tmp_path):
    win, root = _make_win_with_project(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    win._on_source_open("node_0001", "asm")
    log = "\n".join(win._log.toPlainText().splitlines())
    assert "No ASM source assigned" in log


def test_open_source_opens_assigned(tmp_path):
    win, root = _make_win_with_project(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "hello.asm").write_text(_HI_SRC.read_text(encoding="utf-8"),
                                            encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", "src/hello.asm")
    opened = []
    win._editor_tabs.open_tab = lambda part, nid, ext, name: opened.append(name) or name
    win._on_source_open("node_0001", "asm")
    assert opened and opened[0] == "hello.asm"


def test_build_run_uses_assigned_asm(tmp_path):
    win, root = _make_win_with_project(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "hello.asm").write_text(_HI_SRC.read_text(encoding="utf-8"),
                                            encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", "src/hello.asm")
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()
    assert "using assigned asm" in win._log.toPlainText()


def test_build_falls_back_when_no_assignment(tmp_path):
    """No assigned source: existing editor-tab build path still works (UART Hi)."""
    win, root = _make_win_with_project(tmp_path)
    win._editor_tabs.open_tab(_CPU, "node_0001", "asm", "hello.asm")
    from PySide6.QtWidgets import QTextEdit
    editor = win._editor_tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC.read_text(encoding="utf-8"))
    win._build()
    win._do_run()
    assert "Hi" in win._sim_uart.output_text()
