# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_WIRING_V05 — wire mode workflow fix tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QPointF, QEvent, Qt

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode, GridScene

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}

GRID = float(GridScene.GRID_SIZE)


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _two_node_canvas() -> Canvas:
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(200.0, 0.0))
    return c


# ---------------------------------------------------------------------------
# armed (toggle) vs drawing (start point chosen)
# ---------------------------------------------------------------------------

def test_set_mode_wire_is_armed():
    """Ribbon toggle enters wire mode WITHOUT a start point (armed)."""
    c = _canvas()
    c.set_mode("wire")
    assert c._mode == "wire"
    assert c._wire_from is None


def test_begin_wire_from_enters_drawing():
    c = _two_node_canvas()
    c.set_mode("wire")            # armed
    c._begin_wire_from("node_0001", "bus")
    assert c._mode == "wire"
    assert c._wire_from == {"node_id": "node_0001", "port_name": "bus"}
    assert c._wire_preview is not None


def test_begin_wire_from_creates_single_preview():
    """Re-arming replaces the preview instead of leaking a second one."""
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    first = c._wire_preview
    c._begin_wire_from("node_0001", "bus")
    assert first.scene() is None          # old preview removed
    assert c._wire_preview is not None


def test_toggle_then_begin_then_finish_connects():
    """Full flow from the ribbon toggle path produces a connection."""
    c = _two_node_canvas()
    c.set_mode("wire")
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert len(c._connections) == 1
    assert c._mode == "design"            # returns to design after connecting


# ---------------------------------------------------------------------------
# cancel clears everything
# ---------------------------------------------------------------------------

def test_cancel_wire_clears_pending_port():
    c = _two_node_canvas()
    c._pending_port = object()
    c._begin_wire_from("node_0001", "bus")
    c._cancel_wire()
    assert c._pending_port is None


def test_cancel_wire_full_clear():
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    c._add_waypoint(QPointF(60.0, 0.0))
    c._cancel_wire()
    assert c._mode == "design"
    assert c._wire_from is None
    assert c._wire_preview is None
    assert c._wire_waypoints == []
    assert c._handle_items == []


# ---------------------------------------------------------------------------
# Escape key
# ---------------------------------------------------------------------------

def _esc() -> QKeyEvent:
    return QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                     Qt.KeyboardModifier.NoModifier)


def test_escape_cancels_wire():
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    c.keyPressEvent(_esc())
    assert c._mode == "design"
    assert c._wire_from is None


def test_escape_in_design_no_crash():
    c = _canvas()
    c.keyPressEvent(_esc())               # must not raise
    assert c._mode == "design"


# ---------------------------------------------------------------------------
# Canvas decoration
# ---------------------------------------------------------------------------

def test_decoration_on_when_armed():
    c = _canvas()
    c.set_mode("wire")
    assert "border" in c.styleSheet()


def test_decoration_on_when_drawing():
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    assert "border" in c.styleSheet()


def test_decoration_off_in_design():
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    c._cancel_wire()
    assert c.styleSheet() == ""


def test_decoration_off_after_finish():
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    assert c.styleSheet() == ""


# ---------------------------------------------------------------------------
# shared helpers reachable from wire-mode menu
# ---------------------------------------------------------------------------

def test_clone_node_adds_node():
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    node = c.get_node("node_0001")
    before = len(c.get_all_nodes())
    c._clone_node(node)
    assert len(c.get_all_nodes()) == before + 1


def test_select_only_selects_single_node():
    c = _two_node_canvas()
    n1 = c.get_node("node_0001")
    n2 = c.get_node("node_0002")
    n1.setSelected(True)
    c._select_only(n2)
    assert n2.isSelected()
    assert not n1.isSelected()


# ---------------------------------------------------------------------------
# Waypoint still works in wire mode
# ---------------------------------------------------------------------------

def test_add_waypoint_in_drawing_state():
    c = _two_node_canvas()
    c._begin_wire_from("node_0001", "bus")
    c._add_waypoint(QPointF(80.0, 40.0))
    assert len(c._wire_waypoints) == 1


# ---------------------------------------------------------------------------
# MainWin integration: Cancel Wire button + status bar
# ---------------------------------------------------------------------------

def test_mainwin_cancel_wire_action_returns_design():
    from ui.win import MainWin
    win = MainWin()
    win._canvas.set_mode("wire")
    assert win._canvas._mode == "wire"
    win._cancel_wire_action()
    assert win._canvas._mode == "design"


def test_mainwin_mode_changed_sets_statusbar():
    from ui.win import MainWin
    win = MainWin()
    win._on_mode_changed("wire")
    assert win.statusBar().currentMessage() != ""
    assert win._a_wire_mode.isChecked()
    win._on_mode_changed("design")
    assert win.statusBar().currentMessage() == ""
    assert not win._a_wire_mode.isChecked()
