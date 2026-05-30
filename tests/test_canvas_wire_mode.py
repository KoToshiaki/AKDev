# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for wire mode canvas connection UX and Manhattan routing."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QGraphicsPathItem
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine, PartNode, GridScene

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}

GRID = float(GridScene.GRID_SIZE)


def _make_canvas() -> Canvas:
    return Canvas(log_fn=[].append)


# ---------------------------------------------------------------------------
# Default state
# ---------------------------------------------------------------------------

def test_canvas_default_mode_is_design():
    canvas = _make_canvas()
    assert canvas._mode == "design"


def test_canvas_wire_from_default_none():
    canvas = _make_canvas()
    assert canvas._wire_from is None


def test_canvas_wire_waypoints_default_empty():
    canvas = _make_canvas()
    assert canvas._wire_waypoints == []


def test_canvas_wire_preview_default_none():
    canvas = _make_canvas()
    assert canvas._wire_preview is None


# ---------------------------------------------------------------------------
# _start_wire
# ---------------------------------------------------------------------------

def test_start_wire_sets_mode_wire():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    assert canvas._mode == "wire"


def test_start_wire_sets_wire_from():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    assert canvas._wire_from == {"node_id": "node_0001", "port_name": "bus"}


def test_start_wire_creates_preview_item():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    assert canvas._wire_preview is not None


def test_start_wire_preview_in_scene():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    assert canvas._wire_preview in canvas.scene().items()


def test_start_wire_clears_waypoints():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._wire_waypoints = [QPointF(10, 10)]
    canvas._start_wire("node_0001", "bus")
    assert canvas._wire_waypoints == []


# ---------------------------------------------------------------------------
# _cancel_wire
# ---------------------------------------------------------------------------

def test_cancel_wire_resets_mode():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._cancel_wire()
    assert canvas._mode == "design"


def test_cancel_wire_clears_wire_from():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._cancel_wire()
    assert canvas._wire_from is None


def test_cancel_wire_clears_preview_ref():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._cancel_wire()
    assert canvas._wire_preview is None


def test_cancel_wire_removes_preview_from_scene():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    preview_ref = canvas._wire_preview
    canvas._cancel_wire()
    assert preview_ref.scene() is None


def test_cancel_wire_idempotent():
    """Calling _cancel_wire twice must not raise."""
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._cancel_wire()
    canvas._cancel_wire()


# ---------------------------------------------------------------------------
# _finish_wire
# ---------------------------------------------------------------------------

def test_finish_wire_creates_connection():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._finish_wire("node_0002", "bus")
    assert len(canvas._connections) == 1


def test_finish_wire_resets_mode():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._finish_wire("node_0002", "bus")
    assert canvas._mode == "design"


def test_finish_wire_stores_route_key():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._finish_wire("node_0002", "bus")
    assert "route" in canvas._connections[0]


def test_finish_wire_no_waypoints_empty_route():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._finish_wire("node_0002", "bus")
    assert canvas._connections[0]["route"] == []


def test_finish_wire_with_waypoints_stores_route():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    assert len(canvas._connections[0]["route"]) == 1


# ---------------------------------------------------------------------------
# _add_waypoint
# ---------------------------------------------------------------------------

def test_add_waypoint_snaps_to_grid():
    canvas = _make_canvas()
    canvas._add_waypoint(QPointF(33.0, 47.0))
    wp = canvas._wire_waypoints[0]
    assert wp.x() % GRID == pytest.approx(0.0)
    assert wp.y() % GRID == pytest.approx(0.0)


def test_add_waypoint_appended():
    canvas = _make_canvas()
    canvas._add_waypoint(QPointF(40.0, 60.0))
    assert len(canvas._wire_waypoints) == 1


def test_add_two_waypoints():
    canvas = _make_canvas()
    canvas._add_waypoint(QPointF(40.0, 60.0))
    canvas._add_waypoint(QPointF(80.0, 60.0))
    assert len(canvas._wire_waypoints) == 2


# ---------------------------------------------------------------------------
# set_mode
# ---------------------------------------------------------------------------

def test_set_mode_design_from_wire_cancels():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas.set_mode("design")
    assert canvas._mode == "design"
    assert canvas._wire_from is None
    assert canvas._wire_preview is None


def test_set_mode_design_from_design_no_error():
    canvas = _make_canvas()
    canvas.set_mode("design")
    assert canvas._mode == "design"


# ---------------------------------------------------------------------------
# ConnectionLine.update_route — Manhattan routing
# ---------------------------------------------------------------------------

def test_update_route_two_points_not_empty():
    line = ConnectionLine("c1", "n1", "n2")
    line.update_route([QPointF(0.0, 0.0), QPointF(100.0, 60.0)])
    assert not line.path().isEmpty()


def test_update_route_two_points_straight_line():
    """update_route with 2 points draws a straight segment (no implicit H-V elbow)."""
    line = ConnectionLine("c1", "n1", "n2")
    line.update_route([QPointF(0.0, 0.0), QPointF(100.0, 60.0)])
    path = line.path()
    # MoveTo + LineTo = 2 elements (straight line, no inserted corner)
    assert path.elementCount() == 2


def test_update_line_hv_midpoint():
    """update_line creates H-then-V elbow: from (0,0) to (100,60) passes through (100,0)."""
    line = ConnectionLine("c1", "n1", "n2")
    line.update_line(QPointF(0.0, 0.0), QPointF(100.0, 60.0))
    path = line.path()
    # moveTo(0,0), lineTo(100,0), lineTo(100,60)
    assert path.elementCount() == 3
    assert path.elementAt(1).x == pytest.approx(100.0)
    assert path.elementAt(1).y == pytest.approx(0.0)


def test_update_route_single_point_no_crash():
    """Fewer than 2 points: path is unchanged and no exception is raised."""
    line = ConnectionLine("c1", "n1", "n2")
    line.update_route([QPointF(0.0, 0.0)])


def test_update_route_three_points_element_count():
    """Three points produce exactly 3 path elements (straight lineTo chain)."""
    line = ConnectionLine("c1", "n1", "n2")
    line.update_route([QPointF(0.0, 0.0), QPointF(100.0, 0.0), QPointF(100.0, 80.0)])
    assert line.path().elementCount() == 3


def test_update_line_wrapper_not_empty():
    line = ConnectionLine("c1", "n1", "n2")
    line.update_line(QPointF(0.0, 0.0), QPointF(50.0, 30.0))
    assert not line.path().isEmpty()


# ---------------------------------------------------------------------------
# add_connection with route / color
# ---------------------------------------------------------------------------

def test_add_connection_with_route_stores_waypoint():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2",
                                 route=[QPointF(60.0, 0.0)])
    assert len(conn["route"]) == 1
    assert conn["route"][0]["x"] == pytest.approx(60.0)
    assert conn["route"][0]["y"] == pytest.approx(0.0)


def test_add_connection_without_route_empty_list():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2")
    assert conn["route"] == []


def test_add_connection_with_color_stores_color():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2", color="#ff0000")
    assert conn["color"] == "#ff0000"


def test_add_connection_default_color_empty():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2")
    assert conn["color"] == ""


# ---------------------------------------------------------------------------
# import_canvas resets wire mode
# ---------------------------------------------------------------------------

def test_import_canvas_resets_wire_mode():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    assert canvas._mode == "wire"
    canvas.import_canvas({"parts": [], "connections": []}, {}, clear=True)
    assert canvas._mode == "design"
    assert canvas._wire_from is None
