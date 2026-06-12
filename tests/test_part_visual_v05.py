# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PART_VISUAL_V05 — Part Visual stage 1 (color) tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode
from ui.prop import PropPanel, _palette_colors

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}


def _canvas() -> Canvas:
    c = Canvas(log_fn=[].append)
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    return c


# ---------------------------------------------------------------------------
# PartNode color
# ---------------------------------------------------------------------------

def test_partnode_default_color_empty():
    node = PartNode(_PART_A, "node_0001")
    assert node.color() == ""


def test_partnode_set_color_valid():
    node = PartNode(_PART_A, "node_0001")
    assert node.set_color("#ff0000") is True
    assert node.color() == "#ff0000"


def test_partnode_set_color_invalid_rejected():
    node = PartNode(_PART_A, "node_0001")
    node.set_color("#ff0000")
    assert node.set_color("not-a-color") is False
    assert node.color() == "#ff0000"      # unchanged


def test_partnode_clear_color():
    node = PartNode(_PART_A, "node_0001")
    node.set_color("#abcdef")
    assert node.set_color("") is True
    assert node.color() == ""


# ---------------------------------------------------------------------------
# Canvas.set_node_color
# ---------------------------------------------------------------------------

def test_set_node_color_applies():
    c = _canvas()
    assert c.set_node_color("node_0001", "#123456") is True
    assert c.get_node("node_0001").color() == "#123456"


def test_set_node_color_missing_node():
    c = _canvas()
    assert c.set_node_color("ghost", "#123456") is False


def test_set_node_color_invalid_rejected():
    c = _canvas()
    assert c.set_node_color("node_0001", "bogus") is False


def test_set_node_color_empty_reverts():
    c = _canvas()
    c.set_node_color("node_0001", "#123456")
    assert c.set_node_color("node_0001", "") is True
    assert c.get_node("node_0001").color() == ""


# ---------------------------------------------------------------------------
# export / import round-trip
# ---------------------------------------------------------------------------

def test_export_includes_instance_color_when_set():
    c = _canvas()
    c.set_node_color("node_0001", "#0a0b0c")
    entry = c.export_parts()[0]
    assert entry["instance_color"] == "#0a0b0c"


def test_export_omits_color_when_default():
    c = _canvas()
    entry = c.export_parts()[0]
    assert "instance_color" not in entry


def test_import_restores_instance_color():
    c = _canvas()
    c.set_node_color("node_0001", "#0a0b0c")
    data = c.export_parts()
    lib = {_PART_A["id"]: _PART_A}
    c2 = Canvas(log_fn=[].append)
    c2.import_parts(data, lib)
    assert c2.get_node("node_0001").color() == "#0a0b0c"


def test_import_default_has_no_color():
    c = _canvas()
    data = c.export_parts()
    lib = {_PART_A["id"]: _PART_A}
    c2 = Canvas(log_fn=[].append)
    c2.import_parts(data, lib)
    assert c2.get_node("node_0001").color() == ""


# ---------------------------------------------------------------------------
# PropPanel palette + signal
# ---------------------------------------------------------------------------

def test_palette_has_about_100_colors():
    assert len(_palette_colors()) == 100


def test_palette_colors_are_valid_hex():
    from PySide6.QtGui import QColor
    assert all(QColor(c).isValid() for c in _palette_colors())


def test_prop_panel_palette_size():
    panel = PropPanel()
    assert panel.palette_size() == 100


def test_prop_panel_visual_hidden_without_selection():
    panel = PropPanel()
    panel.show_none()
    assert not panel._visual_box.isVisible()


def test_prop_panel_emits_color_changed():
    panel = PropPanel()
    panel.show_part(_PART_A, "node_0001")
    got = []
    panel.color_changed.connect(lambda nid, c: got.append((nid, c)))
    panel._on_swatch("#ff8800")
    assert got == [("node_0001", "#ff8800")]


def test_prop_panel_default_emits_empty():
    panel = PropPanel()
    panel.show_part(_PART_A, "node_0001")
    got = []
    panel.color_changed.connect(lambda nid, c: got.append((nid, c)))
    panel._on_swatch("")
    assert got == [("node_0001", "")]


def test_prop_panel_no_emit_without_node():
    panel = PropPanel()
    panel.show_none()
    got = []
    panel.color_changed.connect(lambda nid, c: got.append((nid, c)))
    panel._on_swatch("#ff8800")
    assert got == []


# ---------------------------------------------------------------------------
# MainWin integration
# ---------------------------------------------------------------------------

def test_mainwin_color_change_updates_node():
    from ui.win import MainWin
    win = MainWin()
    win._canvas.add_part_at(_PART_B, QPointF(0.0, 0.0))
    win._on_part_color_changed("node_0001", "#abcdef")
    assert win._canvas.get_node("node_0001").color() == "#abcdef"
