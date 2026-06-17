# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_ADDRESS_MAP_EDITOR_V08 — GUI base/size override (default = current behaviour)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from core.devices import (
    make_device_spec, assign_mmio_bases, apply_address_overrides, parse_address_int,
)
from core.circuit import (
    build_address_map, build_address_map_from_devices, validate_address_overrides,
    ADDRESS_RANGE_INVALID, ADDRESS_OVERLAP, ADDRESS_MMIO_ALIGN, ADDRESS_MMIO_SIZE,
)
from core.devices import CIRCUIT_COMPAT, MemoryLayout
from ui.win import MainWin
from ui.address_map_editor import AddressMapEditor, COL_MODE, COL_BASE, COL_SIZE, COL_NODE
from core.project import create_project

_CPU  = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}
_RAM  = {"id": "mem.ram",  "name": "RAM",  "category": "mem"}
_UART = {"id": "io.uart",  "name": "UART", "category": "io"}
_HELLO_WORLD  = Path(__file__).parent / "test" / "hello_world.asm"
_RAM_SELFTEST = Path(__file__).parent / "test" / "ram_selftest.asm"


def _codes(issues):
    return {i["code"] for i in issues}


def _ram_uart_specs():
    return assign_mmio_bases([
        make_device_spec("node_0002", _RAM, mode="circuit"),
        make_device_spec("node_0003", _UART, mode="circuit"),
    ])


# ---------------------------------------------------------------------------
# parse_address_int
# ---------------------------------------------------------------------------

def test_parse_address_int():
    assert parse_address_int("0x0100") == 256
    assert parse_address_int("256") == 256
    assert parse_address_int(256) == 256
    assert parse_address_int("0x10") == 16
    import pytest
    for bad in ("", "xyz", "0xZZ", "12.5", None):
        with pytest.raises(ValueError):
            parse_address_int(bad)


# ---------------------------------------------------------------------------
# apply_address_overrides
# ---------------------------------------------------------------------------

def test_apply_no_overrides_noop():
    specs = _ram_uart_specs()
    out = apply_address_overrides(specs, None)
    assert out == specs
    out2 = apply_address_overrides(specs, {})
    assert out2 == specs
    # non-mutating
    assert specs[0]["base"] == 0x0000


def test_apply_base_override():
    specs = _ram_uart_specs()
    out = apply_address_overrides(specs, {"node_0002": {"mode": "manual", "base": 0x0200, "size": 0x8000}})
    ram = next(s for s in out if s["node_id"] == "node_0002")
    assert ram["base"] == 0x0200 and ram["size"] == 0x8000 and ram["end"] == 0x81FF
    assert ram["attach_ranges"] == [(0x0200, 0x81FF)]
    # original untouched
    assert specs[0]["base"] == 0x0000


def test_apply_size_override():
    specs = _ram_uart_specs()
    out = apply_address_overrides(specs, {"node_0003": {"mode": "manual", "base": 0x0100, "size": 0x10}})
    uart = next(s for s in out if s["node_id"] == "node_0003")
    assert uart["size"] == 0x10 and uart["end"] == 0x010F


def test_apply_auto_mode_ignored():
    specs = _ram_uart_specs()
    out = apply_address_overrides(specs, {"node_0002": {"mode": "auto", "base": 0x4000, "size": 0x100}})
    ram = next(s for s in out if s["node_id"] == "node_0002")
    assert ram["base"] == 0x0000 and ram["size"] == 0x10000   # unchanged


def test_apply_then_address_map():
    specs = apply_address_overrides(_ram_uart_specs(),
                                    {"node_0002": {"mode": "manual", "base": 0x0000, "size": 0x10000}})
    # equivalent to auto here -> identical to the wrapper
    a = build_address_map_from_devices("circuit", specs)
    b = build_address_map(mode="circuit", ram_node="node_0002", ram_base=0x0000,
                          ram_size=0x10000, uart_node="node_0003", uart_base=0x0100,
                          uart_size=0x0008)
    assert a == b


# ---------------------------------------------------------------------------
# validate_address_overrides
# ---------------------------------------------------------------------------

def test_validate_clean():
    assert validate_address_overrides(_ram_uart_specs(), {}) == []


def test_validate_base_negative():
    issues = validate_address_overrides(_ram_uart_specs(),
                                        {"node_0002": {"mode": "manual", "base": -1, "size": 0x100}})
    assert ADDRESS_RANGE_INVALID in _codes(issues)


def test_validate_size_zero():
    issues = validate_address_overrides(_ram_uart_specs(),
                                        {"node_0003": {"mode": "manual", "base": 0x0100, "size": 0}})
    assert ADDRESS_RANGE_INVALID in _codes(issues)


def test_validate_end_overflow():
    issues = validate_address_overrides(_ram_uart_specs(),
                                        {"node_0002": {"mode": "manual", "base": 0xFFF0, "size": 0x100}})
    assert ADDRESS_RANGE_INVALID in _codes(issues)   # end > 0xFFFF


def test_validate_overlay_allowed_circuit_compat():
    # UART inside RAM with mmio_inside_ram=True (default) -> overlay, NO overlap error
    issues = validate_address_overrides(_ram_uart_specs(), {}, layout=CIRCUIT_COMPAT)
    assert ADDRESS_OVERLAP not in _codes(issues)


def test_validate_overlap_when_non_overlay():
    layout = MemoryLayout(name="t", ram_base=0x0000, ram_size=0x10000,
                          mmio_base=0x0100, mmio_stride=0x10, mmio_size=0x08,
                          mmio_inside_ram=False, code_base=0x0000, reset_pc=0x0000)
    issues = validate_address_overrides(_ram_uart_specs(), {}, layout=layout)
    assert ADDRESS_OVERLAP in _codes(issues)         # UART region overlaps full RAM


def test_validate_mmio_align_warning():
    issues = validate_address_overrides(_ram_uart_specs(),
                                        {"node_0003": {"mode": "manual", "base": 0x0101, "size": 0x08}})
    assert ADDRESS_MMIO_ALIGN in _codes(issues)
    assert all(i["severity"] != "error" for i in issues if i["code"] == ADDRESS_MMIO_ALIGN)


def test_validate_mmio_size_warning():
    issues = validate_address_overrides(_ram_uart_specs(),
                                        {"node_0003": {"mode": "manual", "base": 0x0100, "size": 0x10}})
    assert ADDRESS_MMIO_SIZE in _codes(issues)


# ---------------------------------------------------------------------------
# MainWin + editor integration
# ---------------------------------------------------------------------------

def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _wire(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")


def _assign(win, root, src, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def test_editor_exists_and_populates(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    assert isinstance(win._address_map_editor, AddressMapEditor)
    win._address_map_editor.refresh()
    # RAM + UART rows (CPU is not addressable -> excluded)
    nodes = {win._address_map_editor._table.item(r, COL_NODE).text()
             for r in range(win._address_map_editor._table.rowCount())}
    assert nodes == {"node_0002", "node_0003"}


def test_no_override_address_map_unchanged(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    _assign(win, root, _HELLO_WORLD, "hello_world.asm")
    win.write_program()
    amap = win._runtime.address_map
    ram = next(d for d in amap["devices"] if d["kind"] == "ram")
    assert ram["attach_ranges"] == [(0x0000, 0x00FF), (0x0108, 0xFFFF)]
    win._do_run()
    assert "Hello World !" in win._sim_uart.output_text()


def test_apply_override_reflected(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    win.apply_address_map_overrides(
        {"node_0003": {"mode": "manual", "base": 0x0110, "size": 0x08}})
    uart = next(d for d in win._runtime.address_map["devices"] if d["kind"] == "uart")
    assert uart["base"] == 0x0110 and uart["end"] == 0x0117
    # RAM carved around the relocated UART window
    ram = next(d for d in win._runtime.address_map["devices"] if d["kind"] == "ram")
    assert (0x0110, 0x0117) in ram["reserved"]


def test_reset_to_auto(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    win.apply_address_map_overrides(
        {"node_0003": {"mode": "manual", "base": 0x0110, "size": 0x08}})
    assert win._address_overrides
    win.reset_address_map_overrides()
    assert win._address_overrides == {}
    uart = next(d for d in win._runtime.address_map["devices"] if d["kind"] == "uart")
    assert uart["base"] == 0x0100              # back to auto


def test_editor_collect_and_apply_via_table(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    ed = win._address_map_editor
    ed.refresh()
    # find the UART row, switch to manual and relocate to 0x0120
    for r in range(ed._table.rowCount()):
        if ed._table.item(r, COL_NODE).text() == "node_0003":
            ed._table.item(r, COL_MODE).setText("manual")
            ed._table.item(r, COL_BASE).setText("0x0120")
            ed._table.item(r, COL_SIZE).setText("0x08")
            break
    overrides, perr = ed.collect_overrides()
    assert perr == []
    assert overrides["node_0003"]["base"] == 0x0120
    ed._on_apply()
    uart = next(d for d in win._runtime.address_map["devices"] if d["kind"] == "uart")
    assert uart["base"] == 0x0120


def test_editor_invalid_blocks_apply(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    ed = win._address_map_editor
    ed.refresh()
    for r in range(ed._table.rowCount()):
        if ed._table.item(r, COL_NODE).text() == "node_0002":   # RAM
            ed._table.item(r, COL_MODE).setText("manual")
            ed._table.item(r, COL_BASE).setText("0xFFF0")
            ed._table.item(r, COL_SIZE).setText("0x0100")       # end > 0xFFFF
            break
    issues = ed._preview()
    assert any(i["severity"] == "error" for i in issues)
    assert ed.has_errors is True
    assert ed._apply_btn.isEnabled() is False


def test_selftest_still_passes(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    _assign(win, root, _RAM_SELFTEST, "ram_selftest.asm")
    win.write_program()
    win._do_run()
    assert "PASS" in win._sim_uart.output_text()


def test_overrides_persist_round_trip(tmp_path):
    win, root = _win(tmp_path)
    _wire(win)
    win.apply_address_map_overrides(
        {"node_0003": {"mode": "manual", "base": 0x0110, "size": 0x08}})  # persists
    # reopen via a fresh MainWin
    from core.project import load_project
    _proj, system = load_project(root)
    assert system.get("address_map_overrides", {}).get("node_0003", {}).get("base") == 0x0110


def test_legacy_mode_unchanged():
    win = MainWin()
    assert win._runtime.address_map["mode"] == "legacy"
    assert win._address_overrides == {}
