# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_ADDRESS_MAP_V07 — explicit Address Map for the virtual circuit devices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.circuit import (
    build_address_map,
    validate_address_map,
    format_address_map_summary,
)
from ui.win import MainWin, _CIRCUIT_RAM_SIZE, _SIM_RAM_SIZE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD = Path(__file__).parent / "test" / "hello_world.asm"
_REL = "tests/test/hello_world.asm"


def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _wire_full(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _assign_hw(win, root):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "hello_world.asm").write_text(
        _HELLO_WORLD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    win._canvas.set_node_source("node_0001", "asm", _REL)


def _dev(amap, kind):
    return next(d for d in amap["devices"] if d["kind"] == kind)


# ---------------------------------------------------------------------------
# build_address_map (pure)
# ---------------------------------------------------------------------------

def test_build_circuit_ram_ranges():
    amap = build_address_map(
        mode="circuit", ram_node="node_0002", ram_base=0x0000, ram_size=0x10000,
        uart_node="node_0003", uart_base=0x0100, uart_size=0x0008,
    )
    ram = _dev(amap, "ram")
    assert ram["base"] == 0x0000
    assert ram["size"] == 0x10000
    assert ram["end"]  == 0xFFFF
    # RAM is attached around the UART MMIO window
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    assert ram["reserved"] == [(0x0100, 0x0107)]


def test_build_circuit_uart_range():
    amap = build_address_map(
        mode="circuit", ram_node="n2", ram_base=0x0000, ram_size=0x10000,
        uart_node="n3", uart_base=0x0100, uart_size=0x0008,
    )
    uart = _dev(amap, "uart")
    assert uart["base"] == 0x0100
    assert uart["size"] == 0x0008
    assert uart["end"]  == 0x0107
    assert uart["attach_ranges"] == [(0x0100, 0x0107)]
    assert uart["role"] == "mmio"
    assert uart["overlay"] == "ram"


def test_build_circuit_is_valid():
    amap = build_address_map(
        mode="circuit", ram_node="n2", ram_base=0x0000, ram_size=0x10000,
        uart_node="n3", uart_base=0x0100, uart_size=0x0008,
    )
    assert validate_address_map(amap) == []


def test_build_legacy_ranges():
    amap = build_address_map(
        mode="legacy", ram_node=None, ram_base=0x0000, ram_size=0x0100,
        uart_node=None, uart_base=0x0100, uart_size=0x0008,
    )
    ram = _dev(amap, "ram")
    uart = _dev(amap, "uart")
    assert ram["size"] == 0x0100
    assert ram["end"]  == 0x00FF
    assert ram["attach_ranges"] == [(0x0000, 0x00FF)]
    assert ram["reserved"] == []
    assert uart["role"] == "io"          # adjacent, not an MMIO overlay
    assert uart["overlay"] is None
    assert validate_address_map(amap) == []


def test_validate_detects_unintended_overlap():
    bad = {
        "mode": "circuit",
        "devices": [
            {"device_id": "a", "kind": "ram",  "attach_ranges": [(0x0000, 0x0FFF)]},
            {"device_id": "b", "kind": "vram", "attach_ranges": [(0x0800, 0x17FF)]},
        ],
    }
    issues = validate_address_map(bad)
    assert len(issues) == 1
    assert "overlap" in issues[0]


def test_format_summary_lines():
    amap = build_address_map(
        mode="circuit", ram_node="node_0002", ram_base=0x0000, ram_size=0x10000,
        uart_node="node_0003", uart_base=0x0100, uart_size=0x0008,
    )
    lines = format_address_map_summary(amap)
    text = "\n".join(lines)
    assert text.startswith("Address Map:")
    assert "RAM" in text and "0x0000-0xffff" in text and "64KB" in text
    assert "UART" in text and "0x0100-0x0107" in text and "MMIO" in text


# ---------------------------------------------------------------------------
# MainWin integration
# ---------------------------------------------------------------------------

def test_circuit_address_map_built(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    assert win.write_program() is True
    amap = win._runtime.address_map
    assert amap is not None
    assert amap["mode"] == "circuit"
    assert win.address_map() is amap


def test_circuit_ram_uart_base_size_end(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    amap = win._runtime.address_map
    ram = _dev(amap, "ram")
    uart = _dev(amap, "uart")
    assert (ram["base"], ram["size"], ram["end"]) == (0x0000, _CIRCUIT_RAM_SIZE, 0xFFFF)
    assert (uart["base"], uart["size"], uart["end"]) == (0x0100, 0x0008, 0x0107)
    assert ram["node_id"] == "node_0002"
    assert uart["node_id"] == "node_0003"


def test_circuit_map_is_valid(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    assert validate_address_map(win._runtime.address_map) == []


def test_bus_matches_address_map(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    # high RAM address reachable; UART window still routes to UART
    win._sim_bus.write(0x2000, 0x12345678)
    assert win._sim_bus.read(0x2000) == 0x12345678
    win._sim_bus.write(0x0100, ord("Q"))
    assert "Q" in win._sim_uart.output_text()


def test_address_map_survives_run(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    before = win._runtime.address_map
    win._do_run()
    assert win._runtime.address_map is before
    assert "Hello World !" in win._sim_uart.output_text()


def test_write_logs_address_map(tmp_path):
    win, root = _win(tmp_path)
    _wire_full(win)
    _assign_hw(win, root)
    win.write_program()
    log = win._log.toPlainText()
    assert "Address Map:" in log


# ---------------------------------------------------------------------------
# legacy mode
# ---------------------------------------------------------------------------

def test_legacy_address_map():
    win = MainWin()                      # no canvas parts → legacy fixed circuit
    amap = win._runtime.address_map
    assert amap is not None
    assert amap["mode"] == "legacy"
    ram = _dev(amap, "ram")
    assert ram["size"] == _SIM_RAM_SIZE
    assert ram["end"] == 0x00FF
    assert _dev(amap, "uart")["overlay"] is None
    assert validate_address_map(amap) == []
