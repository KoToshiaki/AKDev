# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for asm/asm.py — assembler correctness and end-to-end CPU run."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from asm.asm import AsmError, assemble
from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.sim import Bus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RAM_BASE  = 0x0000
RAM_SIZE  = 0x0100   # 256 B — ends at 0x00FF so UART fits right after
UART_BASE = 0x0100   # kept within 16-bit range for LDI compatibility


def _build_system():
    bus  = Bus()
    ram  = RamPart("ram0",  "RAM",  size=RAM_SIZE, base=RAM_BASE)
    uart = UartPart("uart0", "UART", base=UART_BASE)
    cpu  = AK32Part("cpu0",  "AK32", bus, reset_pc=RAM_BASE)
    bus.attach(ram,  RAM_BASE,  RAM_SIZE)
    bus.attach(uart, UART_BASE, 8)
    return bus, ram, uart, cpu


def _run(cpu: AK32Part, *, max_steps: int = 200) -> int:
    for step in range(max_steps):
        cpu.tick()
        if cpu.halted():
            return step + 1
    raise RuntimeError(f"CPU did not halt within {max_steps} steps")


# ---------------------------------------------------------------------------
# Unit tests — encoding
# ---------------------------------------------------------------------------

def test_nop_encodes_to_zero():
    binary = assemble("NOP")
    assert binary == b'\x00\x00\x00\x00'

def test_halt_encodes_correctly():
    binary = assemble("HALT")
    assert binary == b'\x00\x00\x00\x01'

def test_ldi_encoding():
    # LDI r1, 72  →  opcode=0x02 | rd=1 | imm16=72
    binary = assemble("LDI r1, 72")
    word = struct.unpack('<I', binary)[0]
    assert (word >> 24) & 0xFF == 0x02   # opcode LDI
    assert (word >> 16) & 0xFF == 1      # rd = r1
    assert  word        & 0xFFFF == 72   # imm16 = 72

def test_ldi_hex_immediate():
    binary = assemble("LDI r2, 0x100")
    word = struct.unpack('<I', binary)[0]
    assert (word >> 24) & 0xFF == 0x02
    assert (word >> 16) & 0xFF == 2
    assert  word & 0xFFFF == 0x100

def test_out_encoding():
    # OUT [r2], r1  →  opcode=0x03 | ra=2 | rs=1
    binary = assemble("OUT [r2], r1")
    word = struct.unpack('<I', binary)[0]
    assert (word >> 24) & 0xFF == 0x03   # opcode OUT
    assert (word >> 16) & 0xFF == 2      # ra = r2
    assert (word >>  8) & 0xFF == 1      # rs = r1
    assert  word        & 0xFF == 0      # imm8 unused

def test_multiple_instructions_length():
    src = "NOP\nHALT\nLDI r1, 1\nOUT [r1], r1\n"
    binary = assemble(src)
    assert len(binary) == 16  # 4 instructions × 4 bytes

# ---------------------------------------------------------------------------
# Comment, blank line, label
# ---------------------------------------------------------------------------

def test_comment_stripped():
    binary = assemble("NOP  # this is a comment\nHALT")
    assert len(binary) == 8

def test_blank_lines_ignored():
    binary = assemble("\n\nNOP\n\nHALT\n\n")
    assert len(binary) == 8

def test_label_recognised():
    # Labels don't emit code; only instructions count.
    src = """\
start:
    NOP
loop:
    NOP
    HALT
"""
    binary = assemble(src)
    assert len(binary) == 12  # 3 instructions

def test_tokenize_comma_forms():
    # Both "LDI r1,72" and "LDI r1, 72" should work.
    assert assemble("LDI r1,72") == assemble("LDI r1, 72")

# ---------------------------------------------------------------------------
# Error reporting
# ---------------------------------------------------------------------------

def test_error_unknown_mnemonic():
    try:
        assemble("PUSH r1")
        assert False, "should raise AsmError"
    except AsmError as e:
        assert "line 1" in str(e)
        assert "PUSH" in str(e)

def test_error_bad_register():
    try:
        assemble("LDI r16, 0")
        assert False
    except AsmError as e:
        assert "line 1" in str(e)
        assert "r16" in str(e) or "16" in str(e)

def test_error_imm_out_of_range():
    try:
        assemble("LDI r1, 0x10000")   # 65536 > 16-bit max
        assert False
    except AsmError as e:
        assert "line 1" in str(e)

def test_error_bad_deref():
    try:
        assemble("OUT r2, r1")        # missing brackets
        assert False
    except AsmError as e:
        assert "line 1" in str(e)

def test_error_nop_with_operands():
    try:
        assemble("NOP r1")
        assert False
    except AsmError as e:
        assert "NOP" in str(e)

def test_error_line_number_correct():
    src = "NOP\nNOP\nBAD\n"
    try:
        assemble(src)
        assert False
    except AsmError as e:
        assert "line 3" in str(e)

# ---------------------------------------------------------------------------
# End-to-end: assemble → load → run → UART output = "Hi"
# ---------------------------------------------------------------------------

def test_e2e_hi_output():
    src = f"""\
# Print 'H' then 'i' to UART, then halt.
LDI r2, {UART_BASE:#x}    # r2 = UART DATA address
LDI r1, 72                 # 'H' = 72
OUT [r2], r1
LDI r1, 105                # 'i' = 105
OUT [r2], r1
HALT
"""
    binary = assemble(src)
    assert len(binary) == 6 * 4   # 6 instructions

    _, ram, uart, cpu = _build_system()
    ram.load_bytes(binary)
    _run(cpu)

    assert cpu.halted()
    assert uart.output_text() == "Hi"
    print(f"PASS e2e: UART output = {uart.output_text()!r}, pc={cpu.pc():#x}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
