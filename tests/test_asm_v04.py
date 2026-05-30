# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for AK32 v0.4 assembler: ADD/SUB/LD/ST/JMP/BEQ/ADDI + address_map."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from asm.asm import AsmError, assemble, assemble_ex


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _word(binary: bytes, idx: int) -> int:
    """Return the idx-th 32-bit little-endian word."""
    return int.from_bytes(binary[idx * 4: idx * 4 + 4], "little")


# ---------------------------------------------------------------------------
# ADD / SUB / ADDI encoding
# ---------------------------------------------------------------------------

def test_add_encoding():
    binary = assemble("ADD r3, r1, r2")
    assert _word(binary, 0) == (0x04 << 24) | (3 << 16) | (1 << 8) | 2

def test_sub_encoding():
    binary = assemble("SUB r5, r1, r2")
    assert _word(binary, 0) == (0x05 << 24) | (5 << 16) | (1 << 8) | 2

def test_addi_encoding():
    binary = assemble("ADDI r1, r2, 10")
    assert _word(binary, 0) == (0x0A << 24) | (1 << 16) | (2 << 8) | 10

def test_addi_hex_imm():
    binary = assemble("ADDI r1, r1, 0xFF")
    assert _word(binary, 0) == (0x0A << 24) | (1 << 16) | (1 << 8) | 0xFF

def test_addi_imm8_max():
    binary = assemble("ADDI r1, r1, 255")
    assert _word(binary, 0) == (0x0A << 24) | (1 << 16) | (1 << 8) | 255

def test_addi_imm8_overflow_error():
    with pytest.raises(AsmError):
        assemble("ADDI r1, r1, 256")

def test_add_wrong_operand_count():
    with pytest.raises(AsmError):
        assemble("ADD r1, r2")

def test_sub_wrong_operand_count():
    with pytest.raises(AsmError):
        assemble("SUB r1, r2, r3, r4")


# ---------------------------------------------------------------------------
# LD / ST encoding
# ---------------------------------------------------------------------------

def test_ld_encoding():
    binary = assemble("LD r1, [r2]")
    assert _word(binary, 0) == (0x06 << 24) | (1 << 16) | (2 << 8)

def test_st_encoding():
    binary = assemble("ST [r1], r2")
    assert _word(binary, 0) == (0x07 << 24) | (1 << 16) | (2 << 8)

def test_ld_missing_brackets_error():
    with pytest.raises(AsmError):
        assemble("LD r1, r2")   # missing [r2]

def test_st_missing_brackets_error():
    with pytest.raises(AsmError):
        assemble("ST r1, r2")   # missing [r1]

def test_ld_wrong_operand_count():
    with pytest.raises(AsmError):
        assemble("LD r1")


# ---------------------------------------------------------------------------
# JMP encoding
# ---------------------------------------------------------------------------

def test_jmp_immediate():
    binary = assemble("JMP 0x0010")
    assert _word(binary, 0) == (0x08 << 24) | 0x0010

def test_jmp_decimal():
    binary = assemble("JMP 8")
    assert _word(binary, 0) == (0x08 << 24) | 8

def test_jmp_label_forward():
    src = "JMP end\nNOP\nend:\nHALT"
    binary = assemble(src)
    # JMP is at addr 0, NOP at 4, HALT at 8 → target = 8
    assert _word(binary, 0) == (0x08 << 24) | 8

def test_jmp_label_backward():
    src = "NOP\nloop:\nNOP\nJMP loop"
    binary = assemble(src)
    # loop label is at addr 4 (after first NOP)
    assert _word(binary, 2) == (0x08 << 24) | 4

def test_jmp_wrong_operand_count():
    with pytest.raises(AsmError):
        assemble("JMP")

def test_jmp_imm_out_of_range():
    with pytest.raises(AsmError):
        assemble("JMP 0x10000")  # 17-bit value


# ---------------------------------------------------------------------------
# BEQ encoding
# ---------------------------------------------------------------------------

def test_beq_encoding_positive_rel8():
    # BEQ r1, r2, +1  (jump forward 1 word = 4 bytes)
    binary = assemble("BEQ r1, r2, 1")
    assert _word(binary, 0) == (0x09 << 24) | (1 << 16) | (2 << 8) | 1

def test_beq_encoding_zero_rel8():
    binary = assemble("BEQ r1, r2, 0")
    assert _word(binary, 0) == (0x09 << 24) | (1 << 16) | (2 << 8) | 0

def test_beq_encoding_negative_rel8():
    # rel8 = -1 → stored as 0xFF (two's complement)
    binary = assemble("BEQ r1, r2, -1")
    assert _word(binary, 0) == (0x09 << 24) | (1 << 16) | (2 << 8) | 0xFF

def test_beq_label_forward():
    src = """\
BEQ r1, r2, end
NOP
end:
HALT
"""
    binary = assemble(src)
    # BEQ at addr 0, NOP at 4, HALT at 8
    # pc_after_branch = 4, target = 8, offset = (8-4)/4 = 1
    assert (_word(binary, 0) & 0xFF) == 1

def test_beq_label_backward():
    src = """\
NOP
loop:
ADDI r1, r1, 1
BEQ r1, r2, end
JMP loop
end:
HALT
"""
    binary = assemble(src)
    # NOP at 0, loop at 4, ADDI at 4, BEQ at 8, JMP at 12, HALT at 16
    # BEQ pc_after = 12, target (end) = 16, offset = (16-12)/4 = 1
    beq_word = _word(binary, 2)  # 3rd word (index 2)
    rel8 = beq_word & 0xFF
    assert rel8 == 1

def test_beq_rel8_overflow_error():
    # Forward jump of 200 words → rel8 out of range (max +127)
    lines = ["BEQ r1, r2, far_target"] + ["NOP"] * 200 + ["far_target:", "HALT"]
    with pytest.raises(AsmError):
        assemble("\n".join(lines))

def test_beq_wrong_operand_count():
    with pytest.raises(AsmError):
        assemble("BEQ r1, r2")

def test_beq_invalid_label():
    with pytest.raises(AsmError):
        assemble("BEQ r1, r2, nonexistent_label")


# ---------------------------------------------------------------------------
# address_map
# ---------------------------------------------------------------------------

def test_address_map_basic():
    src = "NOP\nHALT"
    _, amap = assemble_ex(src)
    # NOP at addr 0 is source line 0 (0-origin)
    # HALT at addr 4 is source line 1
    assert amap[0] == 0
    assert amap[4] == 1

def test_address_map_with_comments_and_blanks():
    src = "# comment\n\nNOP\nHALT\n"
    _, amap = assemble_ex(src)
    # NOP is on line 2 (0-origin), HALT on line 3
    assert amap[0] == 2
    assert amap[4] == 3

def test_address_map_with_labels():
    src = "NOP\nloop:\nADDI r1, r1, 1\nHALT"
    _, amap = assemble_ex(src)
    # NOP at 0 → line 0, ADDI at 4 → line 2, HALT at 8 → line 3
    assert amap[0] == 0
    assert amap[4] == 2
    assert amap[8] == 3

def test_assemble_returns_bytes_unchanged():
    """assemble() still returns bytes (backward compatible)."""
    result = assemble("NOP\nHALT")
    assert isinstance(result, bytes)
    assert len(result) == 8

def test_assemble_ex_returns_tuple():
    binary, amap = assemble_ex("NOP\nHALT")
    assert isinstance(binary, bytes)
    assert isinstance(amap, dict)

def test_address_map_all_new_instructions():
    src = """\
ADD r1, r2, r3
SUB r1, r2, r3
LD r1, [r2]
ST [r1], r2
ADDI r1, r1, 1
JMP 0x0000
BEQ r1, r2, 0
HALT
"""
    binary, amap = assemble_ex(src)
    assert len(binary) == 8 * 4
    assert len(amap) == 8
    for i in range(8):
        assert i * 4 in amap


# ---------------------------------------------------------------------------
# Regression — existing instructions still work
# ---------------------------------------------------------------------------

def test_nop_still_works():
    assert assemble("NOP") == bytes([0, 0, 0, 0])

def test_halt_still_works():
    assert assemble("HALT") == bytes([0, 0, 0, 1])

def test_ldi_still_works():
    binary = assemble("LDI r1, 72")
    assert _word(binary, 0) == (0x02 << 24) | (1 << 16) | 72

def test_out_still_works():
    binary = assemble("OUT [r2], r1")
    assert _word(binary, 0) == (0x03 << 24) | (2 << 16) | (1 << 8)

def test_hello_asm_assembles():
    """hello.asm still assembles to 6 instructions."""
    src = (Path(__file__).parent.parent / "src" / "hello.asm").read_text()
    binary = assemble(src)
    assert len(binary) == 6 * 4
