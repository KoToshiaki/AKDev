# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for the Build pipeline: EditorTabs → assemble → .bin → CPU run."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from asm.asm import AsmError, assemble
from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.sim import Bus
from ui.editor import CurrentTabInfo, EditorTabs

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RAM_BASE  = 0x0000
RAM_SIZE  = 0x0100
UART_BASE = 0x0100

_HI_SRC = f"""\
LDI r2, {UART_BASE:#x}
LDI r1, 72
OUT [r2], r1
LDI r1, 105
OUT [r2], r1
HALT
"""

_FAKE_PART = {"id": "ak32_cpu", "name": "AK32 CPU"}


def _build_system():
    bus  = Bus()
    ram  = RamPart("ram0",  "RAM",  size=RAM_SIZE, base=RAM_BASE)
    uart = UartPart("uart0", "UART", base=UART_BASE)
    cpu  = AK32Part("cpu0",  "AK32", bus, reset_pc=RAM_BASE)
    bus.attach(ram,  RAM_BASE,  RAM_SIZE)
    bus.attach(uart, UART_BASE, 8)
    return ram, uart, cpu


def _run_cpu(cpu: AK32Part, max_steps: int = 200) -> None:
    for _ in range(max_steps):
        cpu.tick()
        if cpu.halted():
            return
    raise RuntimeError("CPU did not halt")


# ---------------------------------------------------------------------------
# current_tab_info tests
# ---------------------------------------------------------------------------

def test_current_tab_info_none_when_no_tabs(tmp_path):
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    assert tabs.current_tab_info() is None


def test_current_tab_info_returns_correct_fields(tmp_path):
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")

    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    info = tabs.current_tab_info()
    assert isinstance(info, CurrentTabInfo)
    assert info.node_id     == "node_0001"
    assert info.ext         == "asm"
    assert info.text        == _HI_SRC
    assert info.source_name == "main.asm"


def test_current_tab_info_non_asm(tmp_path):
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "node_0001", "v", "cpu.v")
    info = tabs.current_tab_info()
    assert info is not None
    assert info.ext         == "v"
    assert info.source_name == "cpu.v"


# ---------------------------------------------------------------------------
# Build pipeline tests
# ---------------------------------------------------------------------------

def test_build_produces_bin_file(tmp_path):
    """Assemble Hi program → write .bin → file exists with correct size."""
    binary = assemble(_HI_SRC)
    out_dir  = tmp_path / "out"
    out_dir.mkdir()
    out_path = out_dir / "main.bin"
    out_path.write_bytes(binary)

    assert out_path.exists()
    assert len(out_path.read_bytes()) == len(binary)
    assert len(binary) == 6 * 4   # 6 instructions × 4 bytes


def test_build_binary_runs_on_cpu_and_outputs_hi(tmp_path):
    """Full pipeline: assemble → .bin → load into RAM → CPU run → UART = 'Hi'."""
    binary = assemble(_HI_SRC)

    out_dir  = tmp_path / "out"
    out_dir.mkdir()
    out_path = out_dir / "main.bin"
    out_path.write_bytes(binary)

    loaded = out_path.read_bytes()
    ram, uart, cpu = _build_system()
    ram.load_bytes(loaded)
    _run_cpu(cpu)

    assert cpu.halted()
    assert uart.output_text() == "Hi"
    print(f"PASS e2e: UART={uart.output_text()!r}, pc={cpu.pc():#x}")


def test_build_asm_error_reported(tmp_path):
    """assemble() raises AsmError with line info on bad source."""
    bad_src = "NOP\nBAD_MNEM\nHALT"
    try:
        assemble(bad_src)
        assert False, "should raise AsmError"
    except AsmError as e:
        assert "line 2" in str(e)
        assert "BAD_MNEM" in str(e)


def test_build_from_editor_tab(tmp_path):
    """Open a tab, write source, read back via current_tab_info, assemble, run."""
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")

    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    info = tabs.current_tab_info()
    assert info is not None and info.ext == "asm"
    assert info.source_name == "main.asm"

    binary = assemble(info.text)
    ram, uart, cpu = _build_system()
    ram.load_bytes(binary)
    _run_cpu(cpu)

    assert uart.output_text() == "Hi"
    print(f"PASS editor→build→run: UART={uart.output_text()!r}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        with tempfile.TemporaryDirectory() as d:
            try:
                fn(Path(d))
                print(f"  PASS  {fn.__name__}")
                passed += 1
            except Exception as exc:
                print(f"  FAIL  {fn.__name__}: {exc}")
                import traceback; traceback.print_exc()
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
