# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_WIRE_STYLE_V05 — per-connection wire color/width editing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine, _KIND_COLORS, _KIND_PEN_WIDTH
from ui.prop import PropPanel

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_PART_B = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_LIB    = {_PART_A["id"]: _PART_A, _PART_B["id"]: _PART_B}


def _canvas() -> Canvas:
    return Canvas(log_fn=[].append)


def _connected_pair() -> Canvas:
    c = _canvas()
    c.add_part_at(_PART_A, QPointF(0.0, 0.0))
    c.add_part_at(_PART_B, QPointF(300.0, 0.0))
    c._begin_wire_from("node_0001", "bus")
    c._finish_wire("node_0002", "bus")
    return c


def _cid(c: Canvas) -> str:
    return c._connections[0]["id"]


# ---------------------------------------------------------------------------
# ConnectionLine style
# ---------------------------------------------------------------------------

def test_default_uses_kind_color_and_width():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    assert line.base_color().lower() == _KIND_COLORS["bus"].lower()
    assert abs(line.base_width() - _KIND_PEN_WIDTH["bus"]) < 0.01


def test_apply_style_custom_color():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    line.apply_style(color="#ffcc00")
    assert line.base_color().lower() == "#ffcc00"


def test_apply_style_custom_width():
    line = ConnectionLine("c1", "n1", "n2", kind="signal")
    line.apply_style(width=4.0)
    assert abs(line.base_width() - 4.0) < 0.01


def test_apply_style_empty_reverts_to_kind():
    line = ConnectionLine("c1", "n1", "n2", kind="clock")
    line.apply_style(color="#123456", width=9.0)
    line.apply_style("", None)
    assert line.base_color().lower() == _KIND_COLORS["clock"].lower()
    assert abs(line.base_width() - _KIND_PEN_WIDTH["clock"]) < 0.01


def test_priority_selected_over_custom_and_overlays():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    line.apply_style(color="#ffcc00", width=2.0)
    line.set_hovered(True)
    line.set_active(True)
    line.set_selected(True)
    sel_w = line.pen().widthF()
    assert sel_w > line.base_width()       # selected overlay applied on top of custom
    # custom color shows through hover when not selected/active
    line.set_selected(False)
    line.set_active(False)
    assert line.is_hovered() is True
    assert line.pen().widthF() > 2.0       # hover thickens custom base


# ---------------------------------------------------------------------------
# Canvas API
# ---------------------------------------------------------------------------

def test_set_connection_style_returns_true_and_stores():
    c = _connected_pair()
    cid = _cid(c)
    assert c.set_connection_style(cid, color="#ff0000", width=3.0) is True
    conn = c.get_connection(cid)
    assert conn["style"]["color"] == "#ff0000"
    assert conn["style"]["width"] == 3.0
    assert c._conn_items[cid].base_color().lower() == "#ff0000"


def test_set_connection_style_unknown_returns_false():
    c = _connected_pair()
    assert c.set_connection_style("conn_999", color="#ff0000") is False


def test_set_style_empty_color_clears_color_keeps_width():
    c = _connected_pair()
    cid = _cid(c)
    c.set_connection_style(cid, color="#ff0000", width=3.0)
    c.set_connection_style(cid, color="")
    style = c.get_connection(cid)["style"]
    assert "color" not in style
    assert style["width"] == 3.0


def test_reset_connection_style_removes_style():
    c = _connected_pair()
    cid = _cid(c)
    c.set_connection_style(cid, color="#ff0000", width=3.0)
    assert c.reset_connection_style(cid) is True
    assert "style" not in c.get_connection(cid)
    assert c._conn_items[cid].base_color().lower() == _KIND_COLORS["bus"].lower()


def test_reset_connection_style_unknown_returns_false():
    c = _connected_pair()
    assert c.reset_connection_style("conn_999") is False


def test_set_style_preserves_selection():
    c = _connected_pair()
    cid = _cid(c)
    c._set_selected_conn(cid)
    c.set_connection_style(cid, color="#00ff00")
    assert c._selected_conn_id == cid
    assert c._conn_items[cid].is_selected() is True


# ---------------------------------------------------------------------------
# persistence
# ---------------------------------------------------------------------------

def test_export_import_roundtrip_keeps_style():
    c = _connected_pair()
    cid = _cid(c)
    c.set_connection_style(cid, color="#abcdef", width=2.5)
    data = c.export_canvas()
    c2 = _canvas()
    c2.import_canvas(data, _LIB)
    conn = c2._connections[0]
    assert conn["style"]["color"] == "#abcdef"
    assert conn["style"]["width"] == 2.5
    assert c2._conn_items[conn["id"]].base_color().lower() == "#abcdef"


def test_unstyled_connection_has_no_style_key():
    c = _connected_pair()
    data = c.export_canvas()
    assert "style" not in data["connections"][0]


# ---------------------------------------------------------------------------
# Properties panel
# ---------------------------------------------------------------------------

def test_show_wire_switches_panel():
    p = PropPanel()
    p.show_part(_PART_A, "node_0001")
    assert p._wire_box.isHidden()
    p.show_wire({"id": "conn_0001", "kind": "bus",
                 "from": {"node_id": "node_0001", "port": "bus"},
                 "to":   {"node_id": "node_0002", "port": "bus"}})
    assert not p._wire_box.isHidden()
    assert p._visual_box.isHidden()
    assert p._conn_id == "conn_0001"


def test_show_part_after_wire_hides_wire_box():
    p = PropPanel()
    p.show_wire({"id": "conn_0001", "kind": "bus",
                 "from": {"node_id": "n1"}, "to": {"node_id": "n2"}})
    p.show_part(_PART_A, "node_0001")
    assert p._wire_box.isHidden()
    assert p._conn_id == ""


def test_wire_color_signal_emits_conn_id():
    p = PropPanel()
    got = []
    p.wire_color_changed.connect(lambda cid, h: got.append((cid, h)))
    p.show_wire({"id": "conn_0007", "kind": "bus",
                 "from": {"node_id": "n1"}, "to": {"node_id": "n2"}})
    p._on_wire_swatch("#112233")
    assert got == [("conn_0007", "#112233")]


def test_wire_reset_signal():
    p = PropPanel()
    got = []
    p.wire_style_reset.connect(lambda cid: got.append(cid))
    p.show_wire({"id": "conn_0007", "kind": "bus",
                 "from": {"node_id": "n1"}, "to": {"node_id": "n2"}})
    p._on_wire_reset()
    assert got == ["conn_0007"]


def test_wire_palette_nonempty():
    p = PropPanel()
    assert p.wire_palette_size() > 0


def test_palette_applies_color_to_selected_wire():
    """End-to-end-ish: palette signal → canvas API → line base color."""
    c = _connected_pair()
    p = PropPanel()
    cid = _cid(c)
    c._set_selected_conn(cid)
    p.wire_color_changed.connect(
        lambda conn_id, h: c.set_connection_style(conn_id, color=h)
    )
    p.show_wire(c.get_connection(cid))
    p._on_wire_swatch("#ff00ff")
    assert c._conn_items[cid].base_color().lower() == "#ff00ff"


# ---------------------------------------------------------------------------
# regression
# ---------------------------------------------------------------------------

def test_wire_select_delete_still_works():
    c = _connected_pair()
    cid = _cid(c)
    c._set_selected_conn(cid)
    assert c._remove_connection(cid) is True
    assert all(cn["id"] != cid for cn in c._connections)


def test_port_drag_connect_still_works():
    c = _connected_pair()
    before = len(c._connections)
    c.add_part_at({"id": "io.uart", "name": "UART", "category": "io"}, QPointF(0.0, 200.0))
    vp = c.get_node("node_0001").visual_ports()[0]
    c._start_port_drag(c.get_node("node_0001"), vp)
    assert c._finish_port_drag("node_0003") is True
    assert len(c._connections) == before + 1


def test_visual_port_move_still_works():
    c = _connected_pair()
    vp = c.get_node("node_0001").visual_ports()[0]
    c._start_port_move(c.get_node("node_0001"), vp)
    c._update_port_move(QPointF(0.0, 30.0))
    assert vp["side"] == "left"


def test_node_properties_still_works():
    p = PropPanel()
    p.show_part(_PART_A, "node_0001")
    assert not p._visual_box.isHidden()
    assert p._node_id == "node_0001"
    assert p._wire_box.isHidden()
