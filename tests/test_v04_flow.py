# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""v0.4 integration flow test: src/fib.asm → Build → Run → RAM contents.

Validates:
  1. fib.asm assembles without error
  2. assemble_ex() returns a valid address_map
  3. CPU runs to HALT with correct fibonacci values in RAM
  4. Existing hello.asm → UART "Hi" flow still works (regression)
"""
import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from asm.asm import assemble, assemble_ex
from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.sim import Bus

_FIB_ASM   = Path(__file__).parent.parent / "src" / "fib.asm"
_HELLO_ASM = Path(__file__).parent.parent / "src" / "hello.asm"

_RAM_BASE  = 0x0000
_RAM_SIZE  = 0x0100   # 256 bytes
_UART_BASE = 0x0100

# Expected fibonacci values at data area start (0x0040)
_FIB_DATA_BASE = 0x0040
_FIB_EXPECTED  = [0, 1, 1, 2, 3, 5, 8, 13]


def _make_sim():
    bus  = Bus()
    ram  = RamPart("ram", "RAM", size=_RAM_SIZE, base=_RAM_BASE)
    uart = UartPart("uart", "UART", base=_UART_BASE)
    cpu  = AK32Part("cpu", "AK32", bus, reset_pc=_RAM_BASE)
    bus.attach(ram,  _RAM_BASE,  _RAM_SIZE)
    bus.attach(uart, _UART_BASE, 8)
    return bus, ram, uart, cpu


def _run(cpu: AK32Part, max_steps: int = 500) -> None:
    for _ in range(max_steps):
        if cpu.halted():
            break
        cpu.tick()


# ---------------------------------------------------------------------------
# fib.asm file checks
# ---------------------------------------------------------------------------

def test_fib_asm_exists():
    assert _FIB_ASM.exists(), f"missing: {_FIB_ASM}"
    assert _FIB_ASM.stat().st_size > 0


def test_fib_asm_assembles():
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    assert len(binary) % 4 == 0
    assert len(binary) > 0
    # 14 instructions (5 init + loop:6 + BEQ + JMP + HALT)
    assert len(binary) == 14 * 4, f"expected 56 bytes, got {len(binary)}"


def test_fib_asm_address_map():
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary, amap = assemble_ex(src)
    # 14 instructions → 14 entries in address_map
    assert len(amap) == 14
    # Address 0x0000 (first instruction) maps to a line number
    assert 0x0000 in amap
    # All addresses are word-aligned multiples of 4
    for addr in amap:
        assert addr % 4 == 0, f"address {addr:#x} is not word-aligned"


# ---------------------------------------------------------------------------
# fib.asm execution
# ---------------------------------------------------------------------------

def test_fib_runs_to_halt():
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary, _ = assemble_ex(src)
    _, ram, _, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    assert cpu.halted(), "fib.asm did not HALT within step limit"


def test_fib_ram_data_correct():
    """After fib.asm runs, RAM[0x0040..0x005C] contains fibonacci values."""
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    _, ram, _, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    assert cpu.halted()

    for i, expected in enumerate(_FIB_EXPECTED):
        addr = _FIB_DATA_BASE + i * 4
        got = ram.read(addr)
        assert got == expected, (
            f"fib[{i}] at addr {addr:#x}: expected {expected}, got {got}"
        )


def test_fib_r1_is_21_after_halt():
    """After fib loop: r1 = 21 (next a value, not stored)."""
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    _, ram, _, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    # After the loop body's last iteration: a = 21, b = 34
    assert cpu.regs()[1] == 21


def test_fib_count_is_8_after_halt():
    """After fib loop: r5 (count) == 8 (loop limit)."""
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    _, ram, _, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    assert cpu.regs()[5] == 8


def test_fib_write_ptr_advanced():
    """After fib loop: r4 (write ptr) == 0x0040 + 8*4 == 0x0060."""
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    _, ram, _, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    assert cpu.regs()[4] == _FIB_DATA_BASE + 8 * 4


def test_fib_pc_at_halt_instruction():
    """CPU PC points at HALT instruction after fib.asm finishes."""
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary, amap = assemble_ex(src)
    _, ram, _, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    assert cpu.halted()
    halt_pc = cpu.pc()
    # HALT is the last instruction; its address must be in address_map
    assert halt_pc in amap, f"HALT pc {halt_pc:#x} not in address_map"


# ---------------------------------------------------------------------------
# address_map lookups
# ---------------------------------------------------------------------------

def test_fib_address_map_pc_lookup():
    """address_map[pc] returns a valid 0-origin line number."""
    src = _FIB_ASM.read_text(encoding="utf-8")
    binary, amap = assemble_ex(src)
    for addr, line_no in amap.items():
        assert isinstance(line_no, int)
        assert line_no >= 0


# ---------------------------------------------------------------------------
# Regression — hello.asm still works
# ---------------------------------------------------------------------------

def test_hello_asm_still_works():
    """Regression: hello.asm Build → Run → UART 'Hi' is unchanged."""
    src    = _HELLO_ASM.read_text(encoding="utf-8")
    binary = assemble(src)
    _, ram, uart, cpu = _make_sim()
    ram.load_bytes(binary)
    _run(cpu)
    assert cpu.halted()
    assert uart.output_text() == "Hi"
