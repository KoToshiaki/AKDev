# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for AK32 v0.4 instruction set: ADD / SUB / LD / ST / JMP / BEQ / ADDI."""
import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.sim import Bus, BusError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_cpu(program: bytes, *, ram_size: int = 256, ram_base: int = 0):
    """Build a minimal CPU + RAM bus for unit testing."""
    bus  = Bus()
    ram  = RamPart("ram", "RAM", size=ram_size, base=ram_base)
    cpu  = AK32Part("cpu", "AK32", bus, reset_pc=ram_base)
    bus.attach(ram, ram_base, ram_size)
    ram.load_bytes(program)
    return cpu, ram, bus


def _pack(*words: int) -> bytes:
    return b"".join(struct.pack("<I", w & 0xFFFFFFFF) for w in words)


def _run(cpu: AK32Part, max_steps: int = 200) -> None:
    for _ in range(max_steps):
        if cpu.halted():
            break
        cpu.tick()


# ---------------------------------------------------------------------------
# Helpers — instruction word builders
# ---------------------------------------------------------------------------

def _ldi(rd: int, imm16: int) -> int:
    return (0x02 << 24) | (rd << 16) | (imm16 & 0xFFFF)

def _halt() -> int:
    return 0x01_00_00_00

def _add(rd: int, rs: int, rt: int) -> int:
    return (0x04 << 24) | (rd << 16) | (rs << 8) | (rt & 0xFF)

def _sub(rd: int, rs: int, rt: int) -> int:
    return (0x05 << 24) | (rd << 16) | (rs << 8) | (rt & 0xFF)

def _ld(rd: int, rs: int) -> int:
    return (0x06 << 24) | (rd << 16) | (rs << 8)

def _st(rd: int, rs: int) -> int:
    return (0x07 << 24) | (rd << 16) | (rs << 8)

def _jmp(imm16: int) -> int:
    return (0x08 << 24) | (imm16 & 0xFFFF)

def _beq(rs1: int, rs2: int, rel8: int) -> int:
    return (0x09 << 24) | (rs1 << 16) | (rs2 << 8) | (rel8 & 0xFF)

def _addi(rd: int, rs: int, imm8: int) -> int:
    return (0x0A << 24) | (rd << 16) | (rs << 8) | (imm8 & 0xFF)


# ---------------------------------------------------------------------------
# 1.1  ADD instruction
# ---------------------------------------------------------------------------

def test_add_basic():
    """ADD r3, r1, r2 computes r1+r2."""
    prog = _pack(_ldi(1, 10), _ldi(2, 20), _add(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 30
    assert cpu.z_flag() is False

def test_add_z_flag():
    """ADD sets Z when result == 0."""
    prog = _pack(_ldi(1, 0), _ldi(2, 0), _add(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0
    assert cpu.z_flag() is True

def test_add_overflow_wraps():
    """ADD wraps at 32 bits."""
    prog = _pack(_ldi(1, 0xFFFF), _ldi(2, 0x0002), _add(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0x00010001

def test_add_r0_destination_ignored():
    """ADD with rd=r0 leaves r0=0 (hardwired zero)."""
    prog = _pack(_ldi(1, 5), _ldi(2, 7), _add(0, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[0] == 0


# ---------------------------------------------------------------------------
# 1.2  SUB instruction
# ---------------------------------------------------------------------------

def test_sub_basic():
    """SUB r3, r1, r2 computes r1-r2."""
    prog = _pack(_ldi(1, 20), _ldi(2, 7), _sub(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 13
    assert cpu.z_flag() is False

def test_sub_z_flag():
    """SUB sets Z when result == 0."""
    prog = _pack(_ldi(1, 5), _ldi(2, 5), _sub(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0
    assert cpu.z_flag() is True

def test_sub_wraps_32bit():
    """SUB 0 - 1 wraps to 0xFFFFFFFF."""
    prog = _pack(_ldi(1, 0), _ldi(2, 1), _sub(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0xFFFFFFFF


# ---------------------------------------------------------------------------
# 1.3  ADDI instruction
# ---------------------------------------------------------------------------

def test_addi_basic():
    """ADDI r2, r1, 5 adds unsigned imm8."""
    prog = _pack(_ldi(1, 10), _addi(2, 1, 5), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[2] == 15

def test_addi_z_flag():
    """ADDI sets Z when result == 0."""
    prog = _pack(_ldi(1, 0), _addi(2, 1, 0), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[2] == 0
    assert cpu.z_flag() is True

def test_addi_max_imm8():
    """ADDI with imm8=255."""
    prog = _pack(_ldi(1, 0), _addi(2, 1, 255), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[2] == 255

def test_addi_r0_destination_ignored():
    """ADDI with rd=r0 leaves r0=0."""
    prog = _pack(_ldi(1, 3), _addi(0, 1, 10), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[0] == 0


# ---------------------------------------------------------------------------
# 1.4  LD / ST instructions
# ---------------------------------------------------------------------------

def test_st_writes_to_ram():
    """ST [r2], r1 writes r1 to RAM at regs[r2]."""
    prog = _pack(_ldi(1, 0x42), _ldi(2, 0x0040), _st(2, 1), _halt())
    cpu, ram, _ = _make_cpu(prog)
    _run(cpu)
    assert ram.read(0x0040) == 0x42

def test_ld_reads_from_ram():
    """LD r3, [r2] reads word from RAM."""
    prog = _pack(
        _ldi(1, 0xABCD), _ldi(2, 0x0040), _st(2, 1),  # write 0xABCD to 0x0040
        _ld(3, 2),                                      # read it back into r3
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0xABCD

def test_ld_z_flag():
    """LD sets Z when loaded value is 0."""
    prog = _pack(
        _ldi(2, 0x0040),   # addr = 0x0040 (RAM already zeroed)
        _ld(3, 2),
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0
    assert cpu.z_flag() is True

def test_ld_buserror_halts():
    """LD from unmapped address halts the CPU."""
    # RAM is 256 bytes (0x0000-0x00FF); address 0x0200 is unmapped
    prog = _pack(_ldi(2, 0x0200), _ld(3, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.halted()

def test_st_buserror_halts():
    """ST to unmapped address halts the CPU."""
    prog = _pack(_ldi(1, 99), _ldi(2, 0x0200), _st(2, 1), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.halted()

def test_st_r0_destination_is_zero_addr():
    """ST [r0], r1 writes to address 0 (r0 == 0 always)."""
    prog = _pack(_ldi(1, 0xBEEF), _st(0, 1), _halt())
    cpu, ram, _ = _make_cpu(prog)
    _run(cpu)
    # r0=0 → writes to addr 0 (overwrites the LDI instruction, but CPU already past it)
    assert ram.read(0x0000) == 0xBEEF


# ---------------------------------------------------------------------------
# 1.5  JMP instruction
# ---------------------------------------------------------------------------

def test_jmp_skips_instructions():
    """JMP 0x0014 jumps over NOP/HALT pair."""
    # layout: [LDI r1, 1] [JMP 0x0010] [LDI r1, 99] [HALT] [LDI r2, 2] [HALT]
    # 0x0000: LDI r1, 1
    # 0x0004: JMP 0x0010
    # 0x0008: LDI r1, 99   (should be skipped)
    # 0x000C: HALT          (should be skipped)
    # 0x0010: LDI r2, 2
    # 0x0014: HALT
    prog = _pack(
        _ldi(1, 1),
        _jmp(0x0010),
        _ldi(1, 99),
        _halt(),
        _ldi(2, 2),
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[1] == 1    # r1 not overwritten by skipped LDI
    assert cpu.regs()[2] == 2    # r2 set after the jump
    assert cpu.halted()

def test_jmp_absolute_address():
    """JMP target is an absolute address."""
    # Jump to addr 8 (2nd instruction after JMP)
    prog = _pack(
        _jmp(0x0008),   # 0x0000: jump to 0x0008
        _ldi(1, 99),    # 0x0004: skipped
        _ldi(2, 7),     # 0x0008: executed
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[1] == 0    # skipped
    assert cpu.regs()[2] == 7


# ---------------------------------------------------------------------------
# 1.6  BEQ instruction
# ---------------------------------------------------------------------------

def test_beq_taken():
    """BEQ branches when registers are equal."""
    # 0x0000: LDI r1, 5
    # 0x0004: LDI r2, 5
    # 0x0008: BEQ r1, r2, +1  (rel8=1 → jump to 0x0010)
    # 0x000C: LDI r3, 99      (skipped)
    # 0x0010: HALT
    prog = _pack(
        _ldi(1, 5),
        _ldi(2, 5),
        _beq(1, 2, 1),   # rel8=1: pc_after=0x000C, target=0x0010
        _ldi(3, 99),
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0    # LDI r3,99 was skipped
    assert cpu.halted()

def test_beq_not_taken():
    """BEQ falls through when registers are unequal."""
    prog = _pack(
        _ldi(1, 5),
        _ldi(2, 6),
        _beq(1, 2, 1),   # not taken
        _ldi(3, 42),     # executed
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 42

def test_beq_backward_branch():
    """BEQ with negative rel8 branches backward."""
    # 0x0000: LDI r1, 0
    # 0x0004: LDI r2, 3
    # loop (0x0008):
    # 0x0008: ADDI r1, r1, 1
    # 0x000C: BEQ r1, r2, +1  (rel8=1: taken when r1==3, jump to 0x0014)
    # 0x0010: JMP 0x0008       (back to loop)
    # 0x0014: HALT
    prog = _pack(
        _ldi(1, 0),
        _ldi(2, 3),
        _addi(1, 1, 1),
        _beq(1, 2, 1),
        _jmp(0x0008),
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[1] == 3
    assert cpu.halted()

def test_beq_rel8_zero_no_branch_effect():
    """BEQ taken with rel8=0 is a no-op (jumps to next instruction)."""
    # rel8=0 means jump to pc_after_branch (= next instruction anyway)
    prog = _pack(
        _ldi(1, 5),
        _ldi(2, 5),
        _beq(1, 2, 0),   # taken but rel8=0 → pc stays at 0x000C
        _ldi(3, 77),     # still executed
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 77


# ---------------------------------------------------------------------------
# 1.7  r0 hardwired-zero guarantee for all new instructions
# ---------------------------------------------------------------------------

def test_sub_r0_destination_ignored():
    """SUB with rd=r0 leaves r0=0."""
    prog = _pack(_ldi(1, 5), _ldi(2, 3), _sub(0, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[0] == 0

def test_ld_r0_destination_ignored():
    """LD with rd=r0 leaves r0=0."""
    prog = _pack(
        _ldi(1, 0x42), _ldi(2, 0x0040), _st(2, 1),
        _ld(0, 2),
        _halt(),
    )
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[0] == 0


# ---------------------------------------------------------------------------
# 1.8  Unknown opcode halts
# ---------------------------------------------------------------------------

def test_unknown_opcode_halts():
    """An unknown opcode (0xFF) halts the CPU."""
    prog = _pack(0xFF_00_00_00, _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.halted()
