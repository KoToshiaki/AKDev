# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""PATCH_AK32_BITWISE_INSTRUCTIONS_V08 — AND / OR / XOR / NOT bitwise instructions.

Adds four bitwise ops to the AK32 ISA (opcodes 0x0B–0x0E), wired across the three
opcode sites: CPU execute (core/cpu.py), assembler (asm/asm.py) and disassembler
(core/runtime.py:disasm). AND/OR/XOR are 3-operand R-type (like ADD/SUB); NOT is
2-operand. Existing opcodes 0x00–0x0A are unchanged and 0xFF stays unknown→halt.
"""
import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from core.cpu import AK32Part
from core.dev import RamPart, InputPart
from core.sim import Bus
from core.runtime import disasm
from asm.asm import assemble, assemble_ex, AsmError, _OPCODES


# ---------------------------------------------------------------------------
# CPU unit-test fixtures (same style as tests/test_cpu_v04.py)
# ---------------------------------------------------------------------------

def _make_cpu(program: bytes, *, ram_size: int = 256, ram_base: int = 0):
    bus = Bus()
    ram = RamPart("ram", "RAM", size=ram_size, base=ram_base)
    cpu = AK32Part("cpu", "AK32", bus, reset_pc=ram_base)
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


def _ldi(rd, imm16):  return (0x02 << 24) | (rd << 16) | (imm16 & 0xFFFF)
def _halt():          return 0x01_00_00_00
def _and(rd, rs, rt): return (0x0B << 24) | (rd << 16) | (rs << 8) | (rt & 0xFF)
def _or(rd, rs, rt):  return (0x0C << 24) | (rd << 16) | (rs << 8) | (rt & 0xFF)
def _xor(rd, rs, rt): return (0x0D << 24) | (rd << 16) | (rs << 8) | (rt & 0xFF)
def _not(rd, rs):     return (0x0E << 24) | (rd << 16) | (rs << 8)


# ---------------------------------------------------------------------------
# ASM encode
# ---------------------------------------------------------------------------

def test_asm_encode_and():
    assert assemble("AND r1, r2, r3\n") == struct.pack("<I", 0x0B010203)

def test_asm_encode_or():
    assert assemble("OR r1, r2, r3\n") == struct.pack("<I", 0x0C010203)

def test_asm_encode_xor():
    assert assemble("XOR r1, r2, r3\n") == struct.pack("<I", 0x0D010203)

def test_asm_encode_not():
    assert assemble("NOT r1, r2\n") == struct.pack("<I", 0x0E010200)

def test_asm_encode_lowercase_and_comment():
    # Mnemonic case-insensitivity + comment stripping (existing behaviour).
    assert assemble("and r1, r2, r3   # mask\n") == struct.pack("<I", 0x0B010203)


# ---------------------------------------------------------------------------
# ASM operand errors
# ---------------------------------------------------------------------------

def test_asm_and_too_few_operands():
    with pytest.raises(AsmError):
        assemble("AND r1, r2\n")

def test_asm_or_too_few_operands():
    with pytest.raises(AsmError):
        assemble("OR r1, r2\n")

def test_asm_xor_too_few_operands():
    with pytest.raises(AsmError):
        assemble("XOR r1, r2\n")

def test_asm_not_too_many_operands():
    with pytest.raises(AsmError):
        assemble("NOT r1, r2, r3\n")

def test_asm_bad_register():
    with pytest.raises(AsmError):
        assemble("AND r1, r2, r16\n")


# ---------------------------------------------------------------------------
# opcode integrity (CPU constants == assembler table)
# ---------------------------------------------------------------------------

def test_opcode_constants_match_assembler():
    assert AK32Part.OP_AND == _OPCODES["AND"] == 0x0B
    assert AK32Part.OP_OR  == _OPCODES["OR"]  == 0x0C
    assert AK32Part.OP_XOR == _OPCODES["XOR"] == 0x0D
    assert AK32Part.OP_NOT == _OPCODES["NOT"] == 0x0E

def test_existing_opcodes_unchanged():
    # The four new opcodes must not have disturbed the 0x00–0x0A assignments.
    assert _OPCODES["NOP"]  == 0x00 and _OPCODES["HALT"] == 0x01
    assert _OPCODES["ADDI"] == 0x0A and _OPCODES["BEQ"] == 0x09


# ---------------------------------------------------------------------------
# CPU execute
# ---------------------------------------------------------------------------

def test_and_basic():
    prog = _pack(_ldi(1, 0x00F0), _ldi(2, 0x00FF), _and(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0x00F0
    assert cpu.z_flag() is False

def test_or_basic():
    prog = _pack(_ldi(1, 0x00F0), _ldi(2, 0x000F), _or(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0x00FF

def test_xor_basic():
    prog = _pack(_ldi(1, 0x00FF), _ldi(2, 0x0F0F), _xor(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0x0FF0

def test_not_of_zero_is_all_ones():
    prog = _pack(_ldi(1, 0), _not(2, 1), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[2] == 0xFFFFFFFF

def test_not_of_all_ones_is_zero():
    # Build 0xFFFFFFFF via NOT r0 (r0 == 0), then NOT it back to 0.
    prog = _pack(_not(1, 0), _not(2, 1), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[1] == 0xFFFFFFFF
    assert cpu.regs()[2] == 0x00000000

def test_and_z_flag_set_when_zero():
    prog = _pack(_ldi(1, 0xF0), _ldi(2, 0x0F), _and(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0
    assert cpu.z_flag() is True

def test_xor_self_is_zero_z_flag():
    prog = _pack(_ldi(1, 0x1234), _xor(2, 1, 1), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[2] == 0
    assert cpu.z_flag() is True

def test_not_z_flag_set():
    prog = _pack(_not(1, 0), _not(2, 1), _halt())  # r2 = NOT 0xFFFFFFFF = 0
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.z_flag() is True

def test_and_r0_destination_protected():
    prog = _pack(_ldi(1, 0xFF), _ldi(2, 0xFF), _and(0, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[0] == 0

def test_not_r0_destination_protected():
    prog = _pack(_not(0, 1), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[0] == 0

def test_bitwise_32bit_masked():
    # OR of two high-bit values stays within 32 bits.
    prog = _pack(_not(1, 0), _ldi(2, 0x0001), _or(3, 1, 2), _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0xFFFFFFFF

def test_pc_advances_by_four():
    # Single AND then HALT: PC ends pointing at the HALT (0x0008).
    prog = _pack(_and(1, 0, 0), _halt())
    cpu, _, _ = _make_cpu(prog)
    cpu.tick()                       # execute AND at 0x0000
    assert cpu.pc() == 0x0004        # advanced by 4, not branched

def test_unknown_opcode_still_halts():
    # 0xFF remains unassigned -> halt (regression guard for the reserved opcode).
    prog = _pack(0xFF_00_00_00, _halt())
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.halted()


# ---------------------------------------------------------------------------
# disasm
# ---------------------------------------------------------------------------

def test_disasm_bitwise():
    assert disasm(0x0B010203) == "AND r1, r2, r3"
    assert disasm(0x0C010203) == "OR r1, r2, r3"
    assert disasm(0x0D010203) == "XOR r1, r2, r3"
    assert disasm(0x0E010200) == "NOT r1, r2"

def test_disasm_unknown_still_dw():
    assert disasm(0xFF000000) == "DW 0xff000000"


# ---------------------------------------------------------------------------
# assemble + execute round-trip (the assembler output runs on the CPU)
# ---------------------------------------------------------------------------

def test_assemble_and_execute_or():
    prog = assemble("LDI r1, 0x00f0\nLDI r2, 0x000f\nOR r3, r1, r2\nHALT\n")
    cpu, _, _ = _make_cpu(prog)
    _run(cpu)
    assert cpu.regs()[3] == 0x00FF


# ---------------------------------------------------------------------------
# MainWin integration: Input bit-test + ROM target fetch/execute
# ---------------------------------------------------------------------------

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.win import MainWin
from core.project import create_project

_CPU   = {"id": "cpu.ak32", "name": "AK32",  "category": "cpu"}
_RAM   = {"id": "mem.ram",  "name": "RAM",   "category": "mem"}
_UART  = {"id": "io.uart",  "name": "UART",  "category": "io"}
_INPUT = {"id": "io.input", "name": "INPUT", "category": "io"}
_ROM   = {"id": "mem.rom",  "name": "ROM",   "category": "mem"}

# A button = bit4 = 0x10; Input window sits at 0x0110 when a UART occupies 0x0100.
_INPUT_BIT_ASM = (
    "LDI r1, 0x0110\n"
    "LD  r2, [r1]\n"
    "LDI r3, 0x10\n"
    "AND r2, r2, r3\n"
    "BEQ r2, r0, no_a\n"
    "LDI r4, 1\n"
    "HALT\n"
    "no_a:\n"
    "LDI r4, 0\n"
    "HALT\n"
)

_ROM_OR_ASM = "LDI r1, 0x00f0\nLDI r2, 0x000f\nOR r3, r1, r2\nHALT\n"


def _win(tmp_path):
    root = tmp_path / "proj"
    create_project(str(root), "proj")
    win = MainWin()
    win._project_root = root
    win._editor_tabs.set_project_root(root)
    return win, root


def _assign(win, root, text, name):
    dst = root / "tests" / "test"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / name).write_text(text, encoding="utf-8")
    win._canvas.set_node_source("node_0001", "asm", f"tests/test/{name}")


def _wire_with_input(win):
    win._canvas.add_part_at(_CPU,   QPointF(0.0, 0.0))     # node_0001
    win._canvas.add_part_at(_RAM,   QPointF(200.0, 0.0))   # node_0002
    win._canvas.add_part_at(_UART,  QPointF(400.0, 0.0))   # node_0003
    win._canvas.add_part_at(_INPUT, QPointF(600.0, 0.0))   # node_0004
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")


def _wire_with_rom(win):
    win._canvas.add_part_at(_CPU,  QPointF(0.0, 0.0))      # node_0001
    win._canvas.add_part_at(_RAM,  QPointF(200.0, 0.0))    # node_0002
    win._canvas.add_part_at(_UART, QPointF(400.0, 0.0))    # node_0003
    win._canvas.add_part_at(_ROM,  QPointF(600.0, 0.0))    # node_0004
    win._canvas.add_connection("node_0001", "bus", "node_0002", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0003", "bus")
    win._canvas.add_connection("node_0001", "bus", "node_0004", "bus")


def test_input_bit_pressed(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_input(win)
    _assign(win, root, _INPUT_BIT_ASM, "input_bit.asm")
    assert win.write_program() is True
    win.set_input_keys(0x10)            # press A (bit4)
    win._do_run()
    assert win._sim_cpu.regs()[4] == 1   # AND nonzero -> BEQ not taken -> r4 = 1


def test_input_bit_not_pressed(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_input(win)
    _assign(win, root, _INPUT_BIT_ASM, "input_bit.asm")
    win.write_program()
    win.set_input_keys(0x00)            # nothing pressed
    win._do_run()
    assert win._sim_cpu.regs()[4] == 0   # AND zero -> BEQ taken -> r4 = 0


def test_rom_target_bitwise_fetch_execute(tmp_path):
    win, root = _win(tmp_path)
    _wire_with_rom(win)
    # ROM at 0x0000 (size 0x100), RAM shrunk to 0x0200-0xFFFF so nothing overlaps.
    win.apply_address_map_overrides({
        "node_0004": {"mode": "manual", "base": 0x0000, "size": 0x0100},
        "node_0002": {"mode": "manual", "base": 0x0200, "size": 0xFE00},
    })
    win.set_program_target("rom")
    _assign(win, root, _ROM_OR_ASM, "rom_or.asm")
    assert win.write_program() is True
    assert win._sim_cpu.pc() == win._sim_rom.base   # reset PC at ROM base
    win._do_run()
    assert win._sim_cpu.regs()[3] == 0x00FF         # OR executed from ROM
    assert win._sim_cpu.halted() is True
