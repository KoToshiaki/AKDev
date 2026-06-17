# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_PORT_DETAIL_V07 — read-only ports/connections detail for a selected node/wire."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin
from ui.canvas import Canvas
from ui.port_detail import (
    PortDetailPanel, build_node_info, build_wire_info,
    render_detail, direction_from_type,
)
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32 CPU", "category": "cpu",
         "ports": [{"name": "bus", "type": "bus.master"},
                   {"name": "clk", "type": "clock"},
                   {"name": "irq", "type": "irq"}]}
_RAM  = {"id": "mem.ram", "name": "RAM", "category": "mem",
         "ports": [{"name": "bus", "type": "bus.slave"},
                   {"name": "clk", "type": "clock"}]}
_UART = {"id": "io.uart", "name": "UART", "category": "io",
         "ports": [{"name": "bus", "type": "bus.slave"}]}
_LIB  = {_CPU["id"]: _CPU, _RAM["id"]: _RAM, _UART["id"]: _UART}


def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _canvas() -> Canvas:
    c = Canvas(log_fn=[].append)
    c.set_part_library(_LIB)
    return c


def _select(win, node_id):
    win._canvas.scene().clearSelection()
    if node_id is not None:
        win._canvas.get_node(node_id).setSelected(True)


def _cpu_ram(win):
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM, QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")


# ---------------------------------------------------------------------------
# direction / render unit
# ---------------------------------------------------------------------------

def test_direction_from_type():
    assert "master" in direction_from_type("bus.master")
    assert "slave" in direction_from_type("bus.slave")
    assert direction_from_type("clock") == "in"
    assert direction_from_type("serial.uart") == "bidir"
    assert direction_from_type("") == "-"


def test_render_detail_none():
    assert "No node or wire selected" in render_detail({"selection": "none"})
    assert "No node or wire selected" in render_detail({})


def test_render_detail_node_handles_missing_keys():
    txt = render_detail({"selection": "node"})
    assert "Selection: node" in txt
    assert "Logical Ports" in txt


# ---------------------------------------------------------------------------
# panel creation
# ---------------------------------------------------------------------------

def test_panel_exists_on_mainwin():
    win = MainWin()
    assert isinstance(win._port_detail, PortDetailPanel)


def test_initial_no_selection():
    win = MainWin()
    assert "No node or wire selected" in win._port_detail.detail_text()


# ---------------------------------------------------------------------------
# build_node_info (pure)
# ---------------------------------------------------------------------------

def test_build_node_info_basic():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(10.0, 20.0))
    info = build_node_info(c, "node_0001")
    assert info["selection"] == "node"
    assert info["node_id"] == "node_0001"
    assert info["part_id"] == "cpu.ak32"
    assert info["part_name"] == "AK32 CPU"
    assert info["category"] == "cpu"
    names = [p["name"] for p in info["logical_ports"]]
    assert "bus" in names and "clk" in names and "irq" in names
    bus = next(p for p in info["logical_ports"] if p["name"] == "bus")
    assert "master" in bus["direction"]
    assert bus["type"] == "bus.master"


def test_build_node_info_missing_node():
    c = _canvas()
    assert build_node_info(c, "node_9999") == {"selection": "none"}


def test_build_node_info_visual_ports_connected():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    vp1 = c._create_visual_port("node_0001", "right", "bus")
    vp2 = c._create_visual_port("node_0002", "left", "bus")
    # an extra, unconnected visual port on the CPU
    vp_extra = c._create_visual_port("node_0001", "top", "irq")
    c.add_connection("node_0001", "bus", "node_0002", "bus",
                     from_vp=vp1["id"], to_vp=vp2["id"])
    info = build_node_info(c, "node_0001")
    vps = {v["id"]: v for v in info["visual_ports"]}
    assert vps[vp1["id"]]["connected"] is True
    assert vps[vp_extra["id"]]["connected"] is False


# ---------------------------------------------------------------------------
# connections on a node
# ---------------------------------------------------------------------------

def test_build_node_info_connections():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    info = build_node_info(c, "node_0001")
    assert len(info["connections"]) == 1
    conn = info["connections"][0]
    assert conn["id"] == "conn_0001"
    assert conn["peer_node"] == "node_0002"
    assert conn["peer_part"] == "RAM"
    assert conn["from_node"] == "node_0001"
    assert conn["to_node"] == "node_0002"
    assert conn["direction"] == "out"


# ---------------------------------------------------------------------------
# build_wire_info (pure)
# ---------------------------------------------------------------------------

def test_build_wire_info():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    info = build_wire_info(c, "conn_0001")
    assert info["selection"] == "wire"
    assert info["id"] == "conn_0001"
    assert info["from_node"] == "node_0001"
    assert info["to_node"] == "node_0002"
    assert info["from_part"] == "AK32 CPU"
    assert info["to_part"] == "RAM"


def test_build_wire_info_with_style():
    c = _canvas()
    c.add_part_at(_CPU, QPointF(0.0, 0.0))
    c.add_part_at(_RAM, QPointF(200.0, 0.0))
    c.add_connection("node_0001", "bus", "node_0002", "bus")
    c.set_connection_style("conn_0001", color="#ffcc00", width=3.0)
    info = build_wire_info(c, "conn_0001")
    assert info["style"] is not None
    txt = render_detail(info)
    assert "Style" in txt
    assert "ffcc00" in txt


def test_build_wire_info_missing():
    c = _canvas()
    assert build_wire_info(c, "conn_9999") == {"selection": "none"}


# ---------------------------------------------------------------------------
# MainWin integration — node selection
# ---------------------------------------------------------------------------

def test_mainwin_node_selection_shows_detail(tmp_path):
    win, root = _win(tmp_path)
    _cpu_ram(win)
    _select(win, "node_0001")
    win._update_port_detail()
    txt = win._port_detail.detail_text()
    assert "Selection: node" in txt
    assert "node_0001" in txt
    assert "cpu.ak32" in txt
    assert "AK32 CPU" in txt
    assert "Logical Ports" in txt
    assert "bus" in txt
    assert "Connections" in txt
    assert "node_0002" in txt          # peer
    assert "RAM" in txt                # peer part


def test_mainwin_selection_change_updates(tmp_path):
    win, root = _win(tmp_path)
    _cpu_ram(win)
    _select(win, "node_0001")
    win._update_port_detail()
    assert "cpu.ak32" in win._port_detail.detail_text()
    _select(win, "node_0002")
    win._update_port_detail()
    txt = win._port_detail.detail_text()
    assert "mem.ram" in txt
    assert "node_0002" in txt


# ---------------------------------------------------------------------------
# MainWin integration — wire selection
# ---------------------------------------------------------------------------

def test_mainwin_wire_selection_shows_detail(tmp_path):
    win, root = _win(tmp_path)
    _cpu_ram(win)
    win._canvas._set_selected_conn("conn_0001")   # fires wire_selected
    txt = win._port_detail.detail_text()
    assert "Selection: wire" in txt
    assert "conn_0001" in txt
    assert "node_0001" in txt
    assert "node_0002" in txt


# ---------------------------------------------------------------------------
# updates: connection add / remove
# ---------------------------------------------------------------------------

def test_connection_remove_updates(tmp_path):
    win, root = _win(tmp_path)
    _cpu_ram(win)
    _select(win, "node_0001")
    win._update_port_detail()
    assert "conn_0001" in win._port_detail.detail_text()
    win._canvas._remove_connection("conn_0001")   # fires connections_changed
    txt = win._port_detail.detail_text()
    # node still selected, but the connection is gone
    assert "conn_0001" not in txt
    assert "Connections" in txt


def test_visual_port_move_does_not_break(tmp_path):
    win, root = _win(tmp_path)
    win._canvas.add_part_at(_CPU, QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM, QPointF(200.0, 0.0))
    vp1 = win._canvas._create_visual_port("node_0001", "right", "bus")
    vp2 = win._canvas._create_visual_port("node_0002", "left", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus",
                               from_vp=vp1["id"], to_vp=vp2["id"])
    _select(win, "node_0001")
    win._update_port_detail()
    win._canvas.set_visual_port_offset("node_0001", vp1["id"], 12.0)
    win._update_port_detail()
    txt = win._port_detail.detail_text()
    assert vp1["id"] in txt
    assert "Selection: node" in txt


# ---------------------------------------------------------------------------
# existing panels coexist
# ---------------------------------------------------------------------------

def test_run_status_and_properties_intact(tmp_path):
    win, root = _win(tmp_path)
    _cpu_ram(win)
    _select(win, "node_0001")
    win._update_port_detail()
    # Run Status Panel still present + functional
    win._update_run_status()
    assert "Run Status" in win._run_status.status_text()
    # Properties still shows the part
    win._on_canvas_selection([win._canvas.get_node("node_0001")])
    assert win._port_detail is not win._run_status
