# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Canvas Signal Overlay (section 10)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPen

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, ConnectionLine  # noqa: E402


_PART_CPU = {"id": "ak32_cpu", "name": "AK32 CPU", "category": "cpu",
             "description": "", "ports": [], "resources": {}}
_PART_RAM = {"id": "basic_ram", "name": "RAM", "category": "mem",
             "description": "", "ports": [], "resources": {}}

_LIB = {_PART_CPU["id"]: _PART_CPU, _PART_RAM["id"]: _PART_RAM}


def _canvas_with_bus_conn():
    """Return a Canvas with two nodes connected by a bus-kind line."""
    c = Canvas()
    c.resize(400, 300)
    c.set_part_library(_LIB)
    c.add_part(_PART_CPU)
    c.add_part(_PART_RAM)
    nodes = c.get_all_nodes()
    assert len(nodes) >= 2
    c.add_connection(nodes[0].node_id(), "bus",
                     nodes[1].node_id(), "bus", kind="bus")
    return c


# ---------------------------------------------------------------------------
# ConnectionLine.kind() accessor
# ---------------------------------------------------------------------------

def test_kind_accessor_bus():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    assert line.kind() == "bus"


def test_kind_accessor_signal():
    line = ConnectionLine("c1", "n1", "n2", kind="signal")
    assert line.kind() == "signal"


def test_kind_accessor_clock():
    line = ConnectionLine("c1", "n1", "n2", kind="clock")
    assert line.kind() == "clock"


def test_kind_accessor_reset():
    line = ConnectionLine("c1", "n1", "n2", kind="reset")
    assert line.kind() == "reset"


# ---------------------------------------------------------------------------
# ConnectionLine.set_active(True/False)
# ---------------------------------------------------------------------------

def test_set_active_true_changes_pen():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    base_color = line.pen().color().name()
    base_width = line.pen().widthF()
    line.set_active(True)
    assert line.pen().color().name() != base_color or line.pen().widthF() != base_width


def test_set_active_true_wider_pen():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    base_width = line.pen().widthF()
    line.set_active(True)
    assert line.pen().widthF() > base_width


def test_set_active_false_restores_base_color():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    base_color = line.pen().color().name()
    line.set_active(True)
    line.set_active(False)
    assert line.pen().color().name() == base_color


def test_set_active_false_restores_base_width():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    base_width = line.pen().widthF()
    line.set_active(True)
    line.set_active(False)
    assert abs(line.pen().widthF() - base_width) < 0.01


def test_set_active_signal_kind_restores():
    line = ConnectionLine("c1", "n1", "n2", kind="signal")
    base_color = line.pen().color().name()
    line.set_active(True)
    line.set_active(False)
    assert line.pen().color().name() == base_color


def test_set_active_false_to_false_no_crash():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    line.set_active(False)
    line.set_active(False)  # idempotent


def test_set_active_true_to_true_no_crash():
    line = ConnectionLine("c1", "n1", "n2", kind="bus")
    line.set_active(True)
    line.set_active(True)  # idempotent


# ---------------------------------------------------------------------------
# Canvas.update_signal_overlay
# ---------------------------------------------------------------------------

def test_update_signal_overlay_no_crash_empty_canvas():
    c = Canvas()
    c.resize(400, 300)
    c.update_signal_overlay({})


def test_update_signal_overlay_no_crash_with_connections_empty_transactions():
    c = _canvas_with_bus_conn()
    c.update_signal_overlay({})


def test_bus_transaction_activates_bus_lines():
    c = _canvas_with_bus_conn()
    conn_id = c._connections[-1]["id"]
    line = c._conn_items[conn_id]
    base_width = line.pen().widthF()

    transactions = {"sim_ram": ("WRITE", 0x0000, 0x0042)}
    c.update_signal_overlay(transactions)

    assert line.pen().widthF() > base_width


def test_empty_transactions_deactivates_bus_lines():
    c = _canvas_with_bus_conn()
    conn_id = c._connections[-1]["id"]
    line = c._conn_items[conn_id]
    base_color = line.pen().color().name()

    c.update_signal_overlay({"sim_ram": ("WRITE", 0, 0)})
    c.update_signal_overlay({})

    assert line.pen().color().name() == base_color


def test_non_bus_kind_not_affected_by_bus_transactions():
    c = Canvas()
    c.resize(400, 300)
    c.set_part_library(_LIB)
    c.add_part(_PART_CPU)
    c.add_part(_PART_RAM)
    nodes = c.get_all_nodes()
    c.add_connection(nodes[0].node_id(), "bus",
                     nodes[1].node_id(), "bus", kind="signal")

    conn_id = c._connections[-1]["id"]
    line = c._conn_items[conn_id]
    base_width = line.pen().widthF()

    c.update_signal_overlay({"sim_ram": ("WRITE", 0, 0)})

    # signal kind should NOT be activated by bus transactions
    assert abs(line.pen().widthF() - base_width) < 0.01


# ---------------------------------------------------------------------------
# Canvas.clear_signal_overlay
# ---------------------------------------------------------------------------

def test_clear_signal_overlay_no_crash_empty():
    c = Canvas()
    c.resize(400, 300)
    c.clear_signal_overlay()


def test_clear_restores_bus_lines():
    c = _canvas_with_bus_conn()
    conn_id = c._connections[-1]["id"]
    line = c._conn_items[conn_id]
    base_color = line.pen().color().name()

    c.update_signal_overlay({"sim_ram": ("WRITE", 0, 0)})
    c.clear_signal_overlay()

    assert line.pen().color().name() == base_color


# ---------------------------------------------------------------------------
# Bus.last_transactions / reset_transactions
# ---------------------------------------------------------------------------

def test_last_transactions_empty_on_init():
    from core.sim import Bus
    bus = Bus()
    assert bus.last_transactions == {}


def test_write_records_transaction():
    from core.sim import Bus, Part

    class DummyPart(Part):
        def write(self, addr, val):
            pass

    bus = Bus()
    p = DummyPart("dp", "Dummy")
    bus.attach(p, 0x0000, 0x0100)
    bus.write(0x0010, 0x42)
    assert "dp" in bus.last_transactions
    assert bus.last_transactions["dp"] == ("WRITE", 0x0010, 0x42)


def test_read_records_transaction():
    from core.sim import Bus, Part

    class DummyPart(Part):
        def read(self, addr):
            return 0x99

    bus = Bus()
    p = DummyPart("dp", "Dummy")
    bus.attach(p, 0x0000, 0x0100)
    val = bus.read(0x0020)
    assert val == 0x99
    assert bus.last_transactions["dp"] == ("READ", 0x0020, 0x99)


def test_reset_transactions_clears():
    from core.sim import Bus, Part

    class DummyPart(Part):
        def write(self, addr, val):
            pass

    bus = Bus()
    p = DummyPart("dp", "Dummy")
    bus.attach(p, 0x0000, 0x0100)
    bus.write(0x0000, 1)
    assert bus.last_transactions
    bus.reset_transactions()
    assert bus.last_transactions == {}


def test_tracing_still_works_after_last_transactions_added():
    from core.sim import Bus, Part

    class DummyPart(Part):
        def write(self, addr, val):
            pass
        def read(self, addr):
            return 7

    bus = Bus()
    bus.tracing = True
    p = DummyPart("dp", "Dummy")
    bus.attach(p, 0x0000, 0x0100)
    bus.write(0x0000, 5)
    bus.read(0x0000)
    trace = bus.get_trace()
    assert len(trace) == 2
    assert "WRITE" in trace[0]
    assert "READ" in trace[1]


def test_last_transaction_overwritten_by_latest():
    from core.sim import Bus, Part

    class DummyPart(Part):
        def write(self, addr, val):
            pass

    bus = Bus()
    p = DummyPart("dp", "Dummy")
    bus.attach(p, 0x0000, 0x0100)
    bus.write(0x0000, 1)
    bus.write(0x0001, 2)
    # last write wins
    assert bus.last_transactions["dp"] == ("WRITE", 0x0001, 2)


# ---------------------------------------------------------------------------
# MainWin integration — no-crash
# ---------------------------------------------------------------------------

def test_mainwin_step_no_crash():
    from ui.win import MainWin
    win = MainWin()
    win._do_step()


def test_mainwin_run_no_crash():
    from ui.win import MainWin
    from asm.asm import assemble
    win = MainWin()
    # Load a minimal HALT program so Run terminates cleanly.
    binary = assemble("HALT\n")
    win._sim_ram.load_bytes(binary)
    win._do_run()


def test_mainwin_reset_no_crash():
    from ui.win import MainWin
    win = MainWin()
    win._do_reset()


def test_mainwin_reset_clears_transactions():
    from ui.win import MainWin
    win = MainWin()
    win._sim_bus.last_transactions["fake"] = ("WRITE", 0, 0)
    win._do_reset()
    assert win._sim_bus.last_transactions == {}


def test_mainwin_update_signal_overlay_no_crash():
    from ui.win import MainWin
    win = MainWin()
    win._update_signal_overlay()
