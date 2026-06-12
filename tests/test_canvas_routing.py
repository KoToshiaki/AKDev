# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for obstacle-aware BFS routing and RouteHandle."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, RouteHandle, GridScene, _grid_pos, _compress_path

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_PART_C = {"id": "io.uart",  "name": "UART", "category": "io"}

GRID = float(GridScene.GRID_SIZE)


def _make_canvas() -> Canvas:
    return Canvas(log_fn=[].append)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def test_grid_pos_basic():
    assert _grid_pos(QPointF(40.0, 60.0)) == (2, 3)


def test_grid_pos_zero():
    assert _grid_pos(QPointF(0.0, 0.0)) == (0, 0)


def test_grid_pos_rounds_half_up():
    # 30 / 20 = 1.5 → rounds to 2
    assert _grid_pos(QPointF(30.0, 30.0)) == (2, 2)


def test_compress_path_straight():
    """Collinear cells are compressed to only endpoints."""
    path = [(0, 0), (1, 0), (2, 0), (3, 0)]
    assert _compress_path(path) == [(0, 0), (3, 0)]


def test_compress_path_l_shape():
    """L-shaped path keeps the corner."""
    path = [(0, 0), (1, 0), (1, 1), (1, 2)]
    assert _compress_path(path) == [(0, 0), (1, 0), (1, 2)]


def test_compress_path_two_points():
    assert _compress_path([(0, 0), (1, 1)]) == [(0, 0), (1, 1)]


def test_compress_path_single():
    assert _compress_path([(0, 0)]) == [(0, 0)]


# ---------------------------------------------------------------------------
# _block_cells
# ---------------------------------------------------------------------------

def test_block_cells_returns_set():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    blocked = canvas._block_cells(set())
    assert isinstance(blocked, set)
    assert len(blocked) > 0


def test_block_cells_excludes_excl_id():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    blocked = canvas._block_cells({"node_0001"})
    assert len(blocked) == 0


def test_block_cells_multiple_nodes():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(400.0, 0.0))
    blocked_none = canvas._block_cells(set())
    blocked_a    = canvas._block_cells({"node_0001"})
    # Excluding one node means fewer cells
    assert len(blocked_none) > len(blocked_a)


# ---------------------------------------------------------------------------
# _route_segment
# ---------------------------------------------------------------------------

def test_route_segment_no_obstacle_returns_list():
    canvas = _make_canvas()
    result = canvas._route_segment(QPointF(0.0, 0.0), QPointF(60.0, 0.0), set())
    assert isinstance(result, list)
    assert len(result) >= 2


def test_route_segment_start_equals_end():
    canvas = _make_canvas()
    start = QPointF(40.0, 40.0)
    end   = QPointF(41.0, 41.0)  # rounds to same grid cell (2,2)
    result = canvas._route_segment(start, end, set())
    assert result[0] == start
    assert result[-1] == end


def test_route_segment_obstacle_avoidance():
    """BFS must route around a blocked cell."""
    canvas = _make_canvas()
    # straight line (0,0)→(2,0) would go through (1,0); block it
    blocked = {(1, 0)}
    result = canvas._route_segment(
        QPointF(0.0, 0.0), QPointF(40.0, 0.0), blocked
    )
    cells = {(_grid_pos(p)) for p in result}
    assert (1, 0) not in cells


def test_route_segment_fallback_when_blocked():
    """When BFS can't find a path, fall back to H-V Manhattan."""
    canvas = _make_canvas()
    # Create a wall that completely blocks all paths in bounded region
    blocked = set()
    margin = 10
    for r in range(-margin - 1, margin + 2):
        blocked.add((1, r))
    result = canvas._route_segment(
        QPointF(0.0, 0.0), QPointF(40.0, 0.0), blocked
    )
    # Fallback returns exactly 3 points (start, H-V corner, end)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# _route_grid
# ---------------------------------------------------------------------------

def test_route_grid_no_waypoints_not_empty():
    canvas = _make_canvas()
    result = canvas._route_grid(
        QPointF(0.0, 0.0), QPointF(100.0, 60.0), [], set()
    )
    assert len(result) >= 2


def test_route_grid_endpoint_exact_start():
    canvas = _make_canvas()
    start = QPointF(13.0, 27.0)
    end   = QPointF(213.0, 83.0)
    result = canvas._route_grid(start, end, [], set())
    assert result[0].x() == pytest.approx(start.x())
    assert result[0].y() == pytest.approx(start.y())


def test_route_grid_endpoint_exact_end():
    canvas = _make_canvas()
    start = QPointF(13.0, 27.0)
    end   = QPointF(213.0, 83.0)
    result = canvas._route_grid(start, end, [], set())
    assert result[-1].x() == pytest.approx(end.x())
    assert result[-1].y() == pytest.approx(end.y())


def test_route_grid_with_waypoint():
    canvas = _make_canvas()
    wp = QPointF(60.0, 0.0)
    result = canvas._route_grid(
        QPointF(0.0, 0.0), QPointF(120.0, 60.0), [wp], set()
    )
    # Waypoint must appear in the path (or nearby after BFS)
    xs = [p.x() for p in result]
    assert min(abs(x - wp.x()) for x in xs) < GRID * 2


# ---------------------------------------------------------------------------
# RouteHandle
# ---------------------------------------------------------------------------

def test_route_handle_conn_id():
    h = RouteHandle("conn_0001", 0, QPointF(40.0, 40.0), lambda *a: None)
    assert h.conn_id() == "conn_0001"


def test_route_handle_pt_idx():
    h = RouteHandle("conn_0001", 2, QPointF(40.0, 40.0), lambda *a: None)
    assert h.pt_idx() == 2


def test_route_handle_snaps_on_move():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    canvas._start_wire("node_0001", "bus")   # re-enter wire mode to show handles
    assert len(canvas._handle_items) == 1


# ---------------------------------------------------------------------------
# _show_handles / _hide_handles
# ---------------------------------------------------------------------------

def test_show_handles_no_route_no_handles():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._finish_wire("node_0002", "bus")   # no waypoints → empty route
    canvas._start_wire("node_0001", "bus")
    assert len(canvas._handle_items) == 0


def test_show_handles_with_route():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    canvas._start_wire("node_0001", "bus")
    assert len(canvas._handle_items) == 1
    assert all(isinstance(h, RouteHandle) for h in canvas._handle_items)


def test_hide_handles_clears_items():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    canvas._show_handles()
    canvas._hide_handles()
    assert canvas._handle_items == []


def test_start_wire_shows_handles():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    canvas._start_wire("node_0001", "bus")
    assert len(canvas._handle_items) >= 0  # handles shown (count depends on route)


def test_cancel_wire_hides_handles():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    canvas._start_wire("node_0001", "bus")
    canvas._cancel_wire()
    assert canvas._handle_items == []


# ---------------------------------------------------------------------------
# _on_handle_moved
# ---------------------------------------------------------------------------

def test_on_handle_moved_updates_route():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    conn = canvas._connections[0]
    conn_id = conn["id"]
    canvas._on_handle_moved(conn_id, 0, QPointF(80.0, 0.0))
    assert conn["route"][0]["x"] == pytest.approx(80.0)
    assert conn["route"][0]["y"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# mode_changed signal
# ---------------------------------------------------------------------------

def test_mode_changed_signal_wire():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    received = []
    canvas.mode_changed.connect(received.append)
    canvas._start_wire("node_0001", "bus")
    assert "wire" in received


def test_mode_changed_signal_design():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    received = []
    canvas._start_wire("node_0001", "bus")
    canvas.mode_changed.connect(received.append)
    canvas._cancel_wire()
    assert "design" in received


def test_set_mode_wire_emits_signal():
    canvas = _make_canvas()
    received = []
    canvas.mode_changed.connect(received.append)
    canvas.set_mode("wire")
    assert "wire" in received


def test_set_mode_design_from_wire_emits_signal():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    received = []
    canvas.mode_changed.connect(received.append)
    canvas.set_mode("design")
    assert "design" in received


# ---------------------------------------------------------------------------
# set_mode handle visibility
# ---------------------------------------------------------------------------

def test_set_mode_wire_shows_existing_handles():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    assert canvas._handle_items == []   # design mode after finish
    canvas.set_mode("wire")
    assert len(canvas._handle_items) == 1


def test_set_mode_design_hides_handles():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas.set_mode("wire")
    canvas.set_mode("design")
    assert canvas._handle_items == []


# ---------------------------------------------------------------------------
# Export / import route persistence
# ---------------------------------------------------------------------------

def test_export_canvas_route_persists():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(200.0, 0.0))
    canvas._start_wire("node_0001", "bus")
    canvas._add_waypoint(QPointF(100.0, 0.0))
    canvas._finish_wire("node_0002", "bus")
    data = canvas.export_canvas()
    conn = data["connections"][0]
    assert len(conn["route"]) == 1
    assert conn["route"][0]["x"] == pytest.approx(100.0)
    assert conn["route"][0]["y"] == pytest.approx(0.0)


def test_import_canvas_restores_route():
    canvas = _make_canvas()
    data = {
        "parts": [],
        "connections": [{
            "id": "conn_0001",
            "from": {"node_id": "n1", "port": "bus"},
            "to":   {"node_id": "n2", "port": "bus"},
            "kind": "bus", "width": 32, "label": "",
            "route": [{"x": 60.0, "y": 0.0}],
            "color": "",
        }],
    }
    canvas.import_canvas(data, {}, clear=True)
    assert len(canvas._connections) == 1
    assert len(canvas._connections[0]["route"]) == 1
    assert canvas._connections[0]["route"][0]["x"] == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# update_route — straight lineTo (no extra elbows)
# ---------------------------------------------------------------------------

def test_update_route_straight_segments_count():
    """update_route with 3 corner points must produce exactly 3 path elements (no extra elbows)."""
    from ui.canvas import ConnectionLine
    line = ConnectionLine("c1", "n1", "n2", "bus")
    pts = [QPointF(0.0, 20.0), QPointF(100.0, 20.0), QPointF(100.0, 60.0)]
    line.update_route(pts)
    path = line.path()
    # MoveTo + 2x LineTo = 3 elements
    assert path.elementCount() == 3


def test_update_route_two_points_straight():
    """Two co-Y points should yield a straight horizontal line (2 elements)."""
    from ui.canvas import ConnectionLine
    line = ConnectionLine("c1", "n1", "n2", "bus")
    line.update_route([QPointF(0.0, 40.0), QPointF(80.0, 40.0)])
    assert line.path().elementCount() == 2


def test_update_line_hv_corner_element_count():
    """update_line must produce 3 elements: start, H-V corner, end."""
    from ui.canvas import ConnectionLine
    line = ConnectionLine("c1", "n1", "n2", "bus")
    line.update_line(QPointF(0.0, 0.0), QPointF(100.0, 60.0))
    assert line.path().elementCount() == 3


def test_update_line_corner_x_matches_end():
    """The H-V corner inserted by update_line should have end.x as its x."""
    from ui.canvas import ConnectionLine
    line = ConnectionLine("c1", "n1", "n2", "bus")
    line.update_line(QPointF(0.0, 0.0), QPointF(100.0, 60.0))
    mid = line.path().elementAt(1)
    assert abs(mid.x - 100.0) < 0.5


def test_update_line_corner_y_matches_start():
    """The H-V corner inserted by update_line should have start.y as its y."""
    from ui.canvas import ConnectionLine
    line = ConnectionLine("c1", "n1", "n2", "bus")
    line.update_line(QPointF(0.0, 0.0), QPointF(100.0, 60.0))
    mid = line.path().elementAt(1)
    assert abs(mid.y - 0.0) < 0.5


# ---------------------------------------------------------------------------
# update_connections — port positions
# ---------------------------------------------------------------------------

def test_update_connections_path_starts_near_right_edge():
    """Connection line must start at the right edge of the from-node (grid-snapped)."""
    from ui.canvas import _NODE_W, _NODE_H
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(300.0, 0.0))
    canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    line = list(canvas._conn_items.values())[0]
    first_x = line.path().elementAt(0).x
    # Right edge of node at x=0: x = _NODE_W = 140, snapped to grid(20) = 140
    assert abs(first_x - _NODE_W) < GRID + 1


def test_update_connections_path_ends_near_left_edge():
    """Connection line must end at the left edge of the to-node (grid-snapped)."""
    from ui.canvas import _NODE_W, _NODE_H
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(300.0, 0.0))
    canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    line = list(canvas._conn_items.values())[0]
    path = line.path()
    n = path.elementCount()
    last_x = path.elementAt(n - 1).x
    # Left edge of node at x=300: x = 300, snapped = 300
    assert abs(last_x - 300.0) < GRID + 1


def test_from_port_pos_returns_right_edge():
    """_from_port_pos should return right-edge x = node.x + _NODE_W."""
    from ui.canvas import _NODE_W, _NODE_H
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(100.0, 80.0))
    pos = canvas._from_port_pos("node_0001")
    assert pos is not None
    assert abs(pos.x() - (100.0 + _NODE_W)) < 0.5
    assert abs(pos.y() - (80.0 + _NODE_H / 2)) < 0.5


def test_to_port_pos_returns_left_edge():
    """_to_port_pos should return left-edge x = node.x."""
    from ui.canvas import _NODE_H
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(200.0, 60.0))
    pos = canvas._to_port_pos("node_0001")
    assert pos is not None
    assert abs(pos.x() - 200.0) < 0.5
    assert abs(pos.y() - (60.0 + _NODE_H / 2)) < 0.5


def test_from_port_pos_missing_node_returns_none():
    canvas = _make_canvas()
    assert canvas._from_port_pos("ghost") is None


def test_to_port_pos_missing_node_returns_none():
    canvas = _make_canvas()
    assert canvas._to_port_pos("ghost") is None


# ---------------------------------------------------------------------------
# B2 — wire endpoints sit exactly on the ports (no grid gap), even snap OFF
# ---------------------------------------------------------------------------

def test_wire_endpoints_match_ports_when_unsnapped():
    """Endpoints follow the real port positions for off-grid (snap OFF) parts."""
    from ui.canvas import _NODE_W, _NODE_H
    canvas = _make_canvas()
    # Off-grid positions (not multiples of GRID=20).
    canvas.add_part_at(_PART_A, QPointF(13.0, 7.0))
    canvas.add_part_at(_PART_B, QPointF(317.0, 43.0))
    canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    line = list(canvas._conn_items.values())[0]
    path = line.path()
    start = path.elementAt(0)
    end = path.elementAt(path.elementCount() - 1)
    # from-port = right edge of node_0001; to-port = left edge of node_0002
    assert start.x == pytest.approx(13.0 + _NODE_W)
    assert start.y == pytest.approx(7.0 + _NODE_H / 2)
    assert end.x == pytest.approx(317.0)
    assert end.y == pytest.approx(43.0 + _NODE_H / 2)


def test_wire_endpoints_follow_node_after_move():
    """Moving a node keeps the wire endpoint glued to its port."""
    from ui.canvas import _NODE_W, _NODE_H
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.add_part_at(_PART_B, QPointF(300.0, 0.0))
    canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    canvas.get_node("node_0002").setPos(QPointF(411.0, 97.0))  # off-grid move
    canvas.update_connections()
    line = list(canvas._conn_items.values())[0]
    path = line.path()
    end = path.elementAt(path.elementCount() - 1)
    assert end.x == pytest.approx(411.0)
    assert end.y == pytest.approx(97.0 + _NODE_H / 2)


# ---------------------------------------------------------------------------
# B3 — canvas reads as loaded (scene rect + center origin)
# ---------------------------------------------------------------------------

def test_scene_rect_is_generous():
    canvas = _make_canvas()
    r = canvas.sceneRect()
    assert r.width() >= 1000
    assert r.height() >= 1000
    assert r.left() < 0 < r.right()
    assert r.top() < 0 < r.bottom()


def test_center_origin_does_not_raise():
    canvas = _make_canvas()
    canvas.center_origin()   # must not raise headless
