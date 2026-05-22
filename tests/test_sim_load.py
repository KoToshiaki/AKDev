# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for 1.4: assemble → .bin → RAM load → CPU run → UART "Hi"."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from asm.asm import assemble
from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.sim import Bus
from ui.editor import EditorTabs
from ui.win import _SIM_RAM_BASE, _SIM_RAM_SIZE, _SIM_UART_BASE, _SIM_UART_SIZE, _BUILD_OUT

# ---------------------------------------------------------------------------
# Shared constants — must match win.py memory map
# ---------------------------------------------------------------------------

_FAKE_PART = {"id": "ak32_cpu", "name": "AK32 CPU"}

_HI_SRC = f"""\
LDI r2, {_SIM_UART_BASE:#x}
LDI r1, 72
OUT [r2], r1
LDI r1, 105
OUT [r2], r1
HALT
"""


def _make_sim():
    """Reproduce MainWin._setup_sim() exactly for headless testing."""
    bus  = Bus()
    ram  = RamPart("sim_ram",  "RAM",  size=_SIM_RAM_SIZE,  base=_SIM_RAM_BASE)
    uart = UartPart("sim_uart", "UART", base=_SIM_UART_BASE)
    cpu  = AK32Part("sim_cpu",  "AK32", bus, reset_pc=_SIM_RAM_BASE)
    bus.attach(ram,  _SIM_RAM_BASE,  _SIM_RAM_SIZE)
    bus.attach(uart, _SIM_UART_BASE, _SIM_UART_SIZE)
    return ram, uart, cpu


def _run(cpu: AK32Part, max_steps: int = 200) -> None:
    for _ in range(max_steps):
        cpu.tick()
        if cpu.halted():
            return
    raise RuntimeError("CPU did not halt")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sim_memory_map_matches_asm_constants():
    """RAM and UART addresses in win.py must be reachable by a single LDI."""
    assert _SIM_UART_BASE < 0x10000, "UART base must fit in imm16"
    assert _SIM_RAM_BASE  < 0x10000, "RAM base must fit in imm16"
    # UART must not overlap RAM
    assert _SIM_UART_BASE >= _SIM_RAM_BASE + _SIM_RAM_SIZE, (
        "UART overlaps RAM"
    )


def test_make_sim_produces_correct_map():
    """_make_sim() must attach RAM and UART without overlap."""
    ram, uart, cpu = _make_sim()
    assert ram.size  == _SIM_RAM_SIZE
    assert ram.base  == _SIM_RAM_BASE
    assert uart.base == _SIM_UART_BASE


def test_load_binary_into_ram_and_run(tmp_path):
    """Assemble Hi → write .bin → load into RAM → run CPU → UART = 'Hi'."""
    binary = assemble(_HI_SRC)

    # Simulate what _build() does: write .bin file.
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_path = out_dir / "node_0001.bin"
    out_path.write_bytes(binary)

    # Simulate what _build() does after writing: reset + load_bytes.
    ram, uart, cpu = _make_sim()
    ram.reset()
    ram.load_bytes(out_path.read_bytes())
    uart.reset()
    cpu.reset()

    # Manually tick CPU (simulates 1.5 Run).
    _run(cpu)

    assert cpu.halted()
    assert uart.output_text() == "Hi"
    print(f"PASS: UART={uart.output_text()!r}, pc={cpu.pc():#x}")


def test_ram_reset_clears_previous_content():
    """RAM.reset() must erase old binary before a new build is loaded."""
    ram, uart, cpu = _make_sim()

    # First build: load garbage.
    ram.load_bytes(b'\xFF' * 4)
    assert ram.dump()[:4] == b'\xFF\xFF\xFF\xFF'

    # Second build: reset then load real binary.
    binary = assemble(_HI_SRC)
    ram.reset()
    ram.load_bytes(binary)
    uart.reset()
    cpu.reset()

    # The garbage must be gone; CPU must run "Hi" correctly.
    _run(cpu)
    assert uart.output_text() == "Hi"


def test_uart_reset_clears_previous_output():
    """UART must be cleared between builds so old output doesn't accumulate."""
    ram, uart, cpu = _make_sim()
    binary = assemble(_HI_SRC)

    # First run.
    ram.load_bytes(binary)
    _run(cpu)
    assert uart.output_text() == "Hi"

    # Second build cycle: everything is reset.
    ram.reset()
    ram.load_bytes(binary)
    uart.reset()          # <-- must clear "Hi"
    cpu.reset()
    assert uart.output_text() == ""

    # Second run produces fresh "Hi".
    _run(cpu)
    assert uart.output_text() == "Hi"
    print("PASS: UART cleared between builds")


def test_editor_tab_to_sim_full_pipeline(tmp_path):
    """Full pipeline without MainWin: EditorTabs → assemble → RAM → CPU → 'Hi'."""
    EditorTabs._SAVE_DIR = tmp_path

    tabs = EditorTabs()
    tabs.open_tab(_FAKE_PART, "node_0001", "asm")

    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText(_HI_SRC)

    info = tabs.current_tab_info()
    assert info is not None and info.ext == "asm"
    assert info.node_id == "node_0001"

    binary = assemble(info.text)
    assert len(binary) == 6 * 4

    # Write .bin (mirrors _build() behaviour).
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_path = out_dir / f"{info.node_id}.bin"
    out_path.write_bytes(binary)
    assert out_path.exists()

    # Load into sim (mirrors _build() post-write block).
    ram, uart, cpu = _make_sim()
    ram.reset()
    ram.load_bytes(out_path.read_bytes())
    uart.reset()
    cpu.reset()

    _run(cpu)
    assert uart.output_text() == "Hi"
    print(f"PASS pipeline: UART={uart.output_text()!r}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        with tempfile.TemporaryDirectory() as d:
            try:
                fn(Path(d))
                print(f"  PASS  {fn.__name__}")
                passed += 1
            except TypeError:
                # test takes no args
                try:
                    fn()
                    print(f"  PASS  {fn.__name__}")
                    passed += 1
                except Exception as exc:
                    print(f"  FAIL  {fn.__name__}: {exc}")
                    import traceback; traceback.print_exc()
                    failed += 1
            except Exception as exc:
                print(f"  FAIL  {fn.__name__}: {exc}")
                import traceback; traceback.print_exc()
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
