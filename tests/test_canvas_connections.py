# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for Canvas connection data model."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, PartNode

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}


def _make_canvas() -> Canvas:
    logs: list[str] = []
    return Canvas(log_fn=logs.append)


# ---------------------------------------------------------------------------
# Connection ID
# ---------------------------------------------------------------------------

def test_conn_seq_default_zero():
    canvas = _make_canvas()
    assert canvas._conn_seq == 0


def test_conn_id_format():
    canvas = _make_canvas()
    assert canvas._next_conn_id() == "conn_0001"


def test_conn_id_increments():
    canvas = _make_canvas()
    first  = canvas._next_conn_id()
    second = canvas._next_conn_id()
    assert first  == "conn_0001"
    assert second == "conn_0002"


def test_conn_id_four_digit_padding():
    canvas = _make_canvas()
    for _ in range(9):
        canvas._next_conn_id()
    assert canvas._next_conn_id() == "conn_0010"


# ---------------------------------------------------------------------------
# add_connection
# ---------------------------------------------------------------------------

def test_add_connection_returns_dict():
    canvas = _make_canvas()
    result = canvas.add_connection("node_0001", "bus_master", "node_0002", "bus_slave")
    assert isinstance(result, dict)


def test_add_connection_id_field():
    canvas = _make_canvas()
    conn = canvas.add_connection("node_0001", "p1", "node_0002", "p2")
    assert conn["id"] == "conn_0001"


def test_add_connection_from_field():
    canvas = _make_canvas()
    conn = canvas.add_connection("node_0001", "bus_master", "node_0002", "bus_slave")
    assert conn["from"] == {"node_id": "node_0001", "port": "bus_master"}


def test_add_connection_to_field():
    canvas = _make_canvas()
    conn = canvas.add_connection("node_0001", "bus_master", "node_0002", "bus_slave")
    assert conn["to"] == {"node_id": "node_0002", "port": "bus_slave"}


def test_add_connection_default_kind():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2")
    assert conn["kind"] == "bus"


def test_add_connection_default_width():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2")
    assert conn["width"] == 32


def test_add_connection_default_label():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "p1", "n2", "p2")
    assert conn["label"] == ""


def test_add_connection_custom_params():
    canvas = _make_canvas()
    conn = canvas.add_connection("n1", "clk_out", "n2", "clk_in",
                                  kind="clock", width=1, label="SYS_CLK")
    assert conn["kind"]  == "clock"
    assert conn["width"] == 1
    assert conn["label"] == "SYS_CLK"


def test_add_connection_appends_to_list():
    canvas = _make_canvas()
    assert len(canvas._connections) == 0
    canvas.add_connection("n1", "p1", "n2", "p2")
    assert len(canvas._connections) == 1


def test_add_multiple_connections():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    canvas.add_connection("n2", "p3", "n3", "p4")
    assert len(canvas._connections) == 2
    assert canvas._connections[0]["id"] == "conn_0001"
    assert canvas._connections[1]["id"] == "conn_0002"


# ---------------------------------------------------------------------------
# export_canvas
# ---------------------------------------------------------------------------

def test_export_canvas_has_parts_key():
    canvas = _make_canvas()
    data = canvas.export_canvas()
    assert "parts" in data


def test_export_canvas_has_connections_key():
    canvas = _make_canvas()
    data = canvas.export_canvas()
    assert "connections" in data


def test_export_canvas_connections_list():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    data = canvas.export_canvas()
    assert isinstance(data["connections"], list)
    assert len(data["connections"]) == 1


def test_export_canvas_connection_content():
    canvas = _make_canvas()
    canvas.add_connection("node_0001", "bus_master", "node_0002", "bus_slave",
                          kind="bus", width=32, label="AK32 Bus")
    conn = canvas.export_canvas()["connections"][0]
    assert conn["id"]    == "conn_0001"
    assert conn["from"]  == {"node_id": "node_0001", "port": "bus_master"}
    assert conn["to"]    == {"node_id": "node_0002", "port": "bus_slave"}
    assert conn["kind"]  == "bus"
    assert conn["width"] == 32
    assert conn["label"] == "AK32 Bus"


def test_export_canvas_parts_included():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    data = canvas.export_canvas()
    assert len(data["parts"]) == 1
    assert data["parts"][0]["part_id"] == _PART_A["id"]


def test_export_canvas_empty_canvas():
    canvas = _make_canvas()
    data = canvas.export_canvas()
    assert data["parts"] == []
    assert data["connections"] == []


# ---------------------------------------------------------------------------
# import_canvas
# ---------------------------------------------------------------------------

_CONN_ENTRY = {
    "id":    "conn_0001",
    "from":  {"node_id": "node_0001", "port": "bus_master"},
    "to":    {"node_id": "node_0002", "port": "bus_slave"},
    "kind":  "bus",
    "width": 32,
    "label": "",
}


def test_import_canvas_restores_connections():
    canvas = _make_canvas()
    canvas.import_canvas({"parts": [], "connections": [_CONN_ENTRY]}, {})
    assert len(canvas._connections) == 1
    assert canvas._connections[0]["id"] == "conn_0001"


def test_import_canvas_clear_resets_connections():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    canvas.import_canvas({"parts": [], "connections": []}, {}, clear=True)
    assert len(canvas._connections) == 0


def test_import_canvas_clear_resets_conn_seq():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")   # seq → 1
    canvas.import_canvas({"parts": [], "connections": []}, {}, clear=True)
    assert canvas._conn_seq == 0


def test_import_canvas_no_clear_appends():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")   # conn_0001
    extra = {
        "id": "conn_0002",
        "from": {"node_id": "n2", "port": "p2"},
        "to":   {"node_id": "n3", "port": "p3"},
        "kind": "signal", "width": 1, "label": "",
    }
    canvas.import_canvas({"parts": [], "connections": [extra]}, {}, clear=False)
    assert len(canvas._connections) == 2


def test_import_canvas_updates_conn_seq():
    canvas = _make_canvas()
    high_conn = {
        "id": "conn_0042",
        "from": {"node_id": "n1", "port": "p1"},
        "to":   {"node_id": "n2", "port": "p2"},
        "kind": "bus", "width": 32, "label": "",
    }
    canvas.import_canvas({"parts": [], "connections": [high_conn]}, {})
    assert canvas._conn_seq >= 42


def test_import_canvas_roundtrip():
    """export_canvas → import_canvas → export_canvas must be idempotent."""
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(20.0, 40.0))
    canvas.add_connection("node_0001", "bus_master", "node_0001", "debug",
                          kind="signal", width=1, label="")
    snapshot = canvas.export_canvas()

    canvas2 = _make_canvas()
    canvas2.import_canvas(snapshot, _LIB)
    restored = canvas2.export_canvas()

    assert len(restored["parts"])       == len(snapshot["parts"])
    assert len(restored["connections"]) == len(snapshot["connections"])
    assert restored["connections"][0]["id"] == snapshot["connections"][0]["id"]


# ---------------------------------------------------------------------------
# Backward compatibility — export_parts / import_parts must be unbroken
# ---------------------------------------------------------------------------

def test_export_parts_still_works():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    parts = canvas.export_parts()
    assert len(parts) == 1
    assert parts[0]["part_id"] == _PART_A["id"]


def test_import_parts_still_works():
    canvas = _make_canvas()
    parts = [{
        "node_id": "node_0001",
        "part_id": _PART_A["id"],
        "x": 0.0, "y": 0.0,
        "sources": {"asm": None, "hdl": None},
    }]
    canvas.import_parts(parts, _LIB)
    nodes = [i for i in canvas.scene().items() if isinstance(i, PartNode)]
    assert len(nodes) == 1


def test_import_parts_does_not_touch_connections():
    canvas = _make_canvas()
    canvas.add_connection("n1", "p1", "n2", "p2")
    canvas.import_parts([], _LIB, clear=False)
    assert len(canvas._connections) == 1


def test_connections_independent_of_node_seq():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))   # node_seq → 1
    canvas.add_connection("n1", "p1", "n2", "p2")     # conn_seq → 1
    assert canvas._node_seq == 1
    assert canvas._conn_seq == 1
    assert canvas._next_node_id() == "node_0002"
    assert canvas._next_conn_id() == "conn_0002"
