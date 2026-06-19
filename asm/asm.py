# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AK32 assembler — NOP / HALT / LDI / OUT / ADD / SUB / LD / ST / JMP / BEQ / ADDI / AND / OR / XOR / NOT.

Instruction encoding (32-bit fixed length, little-endian output)
-----------------------------------------------------------------
bits 31..24  opcode
bits 23..16  rd / rs  (destination or compare reg 1)
bits 15..8   rs / rt  (source reg or compare reg 2)
bits  7..0   rt / imm8 / rel8

Opcodes
-------
NOP=0x00  HALT=0x01  LDI=0x02  OUT=0x03
ADD=0x04  SUB=0x05  LD=0x06   ST=0x07
JMP=0x08  BEQ=0x09  ADDI=0x0A
AND=0x0B  OR=0x0C   XOR=0x0D   NOT=0x0E   (PATCH_AK32_BITWISE_INSTRUCTIONS_V08)
"""
from __future__ import annotations

import re
import struct

# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class AsmError(Exception):
    """Assembler error with line number."""

    def __init__(self, lineno: int, message: str):
        super().__init__(f"line {lineno}: {message}")
        self.lineno = lineno


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

_RE_REG   = re.compile(r'^r(\d+)$', re.IGNORECASE)
_RE_DEREF = re.compile(r'^\[r(\d+)\]$', re.IGNORECASE)


def _parse_reg(token: str, lineno: int) -> int:
    m = _RE_REG.match(token)
    if not m:
        raise AsmError(lineno, f"expected register r0-r15, got {token!r}")
    n = int(m.group(1))
    if not (0 <= n <= 15):
        raise AsmError(lineno, f"register r{n} out of range (r0-r15)")
    return n


def _parse_deref(token: str, lineno: int) -> int:
    m = _RE_DEREF.match(token)
    if not m:
        raise AsmError(lineno, f"expected [rN], got {token!r}")
    n = int(m.group(1))
    if not (0 <= n <= 15):
        raise AsmError(lineno, f"register r{n} out of range (r0-r15)")
    return n


def _parse_imm(token: str, lineno: int, *, bits: int = 16) -> int:
    try:
        value = int(token, 0)   # handles decimal and 0x hex
    except ValueError:
        raise AsmError(lineno, f"invalid immediate {token!r}")
    limit = 1 << bits
    if not (0 <= value < limit):
        raise AsmError(
            lineno,
            f"immediate {value} ({value:#x}) out of range for "
            f"{bits}-bit unsigned (0..{limit - 1})",
        )
    return value


def _strip_comment(line: str) -> str:
    idx = line.find('#')
    return line[:idx] if idx >= 0 else line


def _tokenize(line: str) -> list[str]:
    """Split a stripped source line on whitespace and commas."""
    return [t for t in re.split(r'[\s,]+', line.strip()) if t]


def _pack(word: int) -> bytes:
    return struct.pack('<I', word & 0xFFFFFFFF)


def _resolve_addr(token: str, labels: dict[str, int], lineno: int) -> int:
    """Resolve a label name or integer literal to an absolute address."""
    if token in labels:
        return labels[token]
    return _parse_imm(token, lineno, bits=16)


def _resolve_rel8(
    token: str, labels: dict[str, int], instr_pc: int, lineno: int
) -> int:
    """Resolve BEQ branch target to signed rel8 (word offset from pc_after_branch).

    pc_after_branch = instr_pc + 4.
    Returned value is the unsigned byte representation (two's complement, 0..255).
    """
    if token in labels:
        target = labels[token]
        diff = target - (instr_pc + 4)
        if diff % 4 != 0:
            raise AsmError(lineno, f"branch target 0x{target:04x} is not word-aligned")
        offset = diff // 4
    else:
        try:
            offset = int(token, 0)
        except ValueError:
            raise AsmError(lineno, f"invalid branch target {token!r}")
    if not (-128 <= offset <= 127):
        raise AsmError(lineno, f"branch offset {offset} out of range (-128..127)")
    return offset & 0xFF  # two's complement unsigned byte


# ---------------------------------------------------------------------------
# All known mnemonics (used in pass 1 to validate / advance PC)
# ---------------------------------------------------------------------------

_OPCODES = {
    'NOP':  0x00, 'HALT': 0x01, 'LDI':  0x02, 'OUT':  0x03,
    'ADD':  0x04, 'SUB':  0x05, 'LD':   0x06, 'ST':   0x07,
    'JMP':  0x08, 'BEQ':  0x09, 'ADDI': 0x0A,
    # PATCH_AK32_BITWISE_INSTRUCTIONS_V08
    'AND':  0x0B, 'OR':   0x0C, 'XOR':  0x0D, 'NOT':  0x0E,
}


# ---------------------------------------------------------------------------
# Core assembler implementation
# ---------------------------------------------------------------------------


def assemble_ex(text: str) -> tuple[bytes, dict[int, int]]:
    """Assemble *text* and return ``(binary, address_map)``.

    ``address_map[byte_addr]`` is the 0-origin source line number of the
    instruction at that address (for PC-highlight in the editor).

    Raises :class:`AsmError` on any syntax or range error.
    """
    lines = text.splitlines()

    # ------------------------------------------------------------------
    # Pass 1 — collect labels and build address_map
    # ------------------------------------------------------------------
    labels:      dict[str, int] = {}
    address_map: dict[int, int] = {}
    pc = 0
    for lineno, raw in enumerate(lines, 1):
        stripped = _strip_comment(raw).strip()
        if not stripped:
            continue
        if stripped.endswith(':'):
            label = stripped[:-1]
            if not label.isidentifier():
                raise AsmError(lineno, f"invalid label name {label!r}")
            if label in labels:
                raise AsmError(lineno, f"duplicate label {label!r}")
            labels[label] = pc
            continue
        tokens = _tokenize(stripped)
        if tokens:
            mnem = tokens[0].upper()
            if mnem not in _OPCODES:
                raise AsmError(lineno, f"unknown mnemonic {tokens[0]!r}")
            address_map[pc] = lineno - 1  # 0-origin line number
            pc += 4

    # ------------------------------------------------------------------
    # Pass 2 — encode instructions
    # ------------------------------------------------------------------
    result = bytearray()
    pc = 0
    for lineno, raw in enumerate(lines, 1):
        stripped = _strip_comment(raw).strip()
        if not stripped or stripped.endswith(':'):
            continue

        tokens = _tokenize(stripped)
        if not tokens:
            continue

        mnem = tokens[0].upper()
        args = tokens[1:]

        if mnem == 'NOP':
            if args:
                raise AsmError(lineno, "NOP takes no operands")
            result += _pack(0x00_00_00_00)

        elif mnem == 'HALT':
            if args:
                raise AsmError(lineno, "HALT takes no operands")
            result += _pack(0x01_00_00_00)

        elif mnem == 'LDI':
            if len(args) != 2:
                raise AsmError(lineno, f"LDI requires 2 operands, got {len(args)}")
            rd    = _parse_reg(args[0], lineno)
            imm16 = _parse_imm(args[1], lineno, bits=16)
            result += _pack((0x02 << 24) | (rd << 16) | imm16)

        elif mnem == 'OUT':
            if len(args) != 2:
                raise AsmError(lineno, f"OUT requires 2 operands, got {len(args)}")
            ra = _parse_deref(args[0], lineno)
            rs = _parse_reg(args[1], lineno)
            result += _pack((0x03 << 24) | (ra << 16) | (rs << 8))

        elif mnem == 'ADD':
            if len(args) != 3:
                raise AsmError(lineno, f"ADD requires 3 operands, got {len(args)}")
            rd = _parse_reg(args[0], lineno)
            rs = _parse_reg(args[1], lineno)
            rt = _parse_reg(args[2], lineno)
            result += _pack((0x04 << 24) | (rd << 16) | (rs << 8) | rt)

        elif mnem == 'SUB':
            if len(args) != 3:
                raise AsmError(lineno, f"SUB requires 3 operands, got {len(args)}")
            rd = _parse_reg(args[0], lineno)
            rs = _parse_reg(args[1], lineno)
            rt = _parse_reg(args[2], lineno)
            result += _pack((0x05 << 24) | (rd << 16) | (rs << 8) | rt)

        elif mnem == 'LD':
            if len(args) != 2:
                raise AsmError(lineno, f"LD requires 2 operands, got {len(args)}")
            rd = _parse_reg(args[0], lineno)
            rs = _parse_deref(args[1], lineno)
            result += _pack((0x06 << 24) | (rd << 16) | (rs << 8))

        elif mnem == 'ST':
            if len(args) != 2:
                raise AsmError(lineno, f"ST requires 2 operands, got {len(args)}")
            rd = _parse_deref(args[0], lineno)
            rs = _parse_reg(args[1], lineno)
            result += _pack((0x07 << 24) | (rd << 16) | (rs << 8))

        elif mnem == 'JMP':
            if len(args) != 1:
                raise AsmError(lineno, f"JMP requires 1 operand, got {len(args)}")
            addr = _resolve_addr(args[0], labels, lineno)
            result += _pack((0x08 << 24) | addr)

        elif mnem == 'BEQ':
            if len(args) != 3:
                raise AsmError(lineno, f"BEQ requires 3 operands, got {len(args)}")
            rs_reg = _parse_reg(args[0], lineno)
            rt_reg = _parse_reg(args[1], lineno)
            rel8   = _resolve_rel8(args[2], labels, pc, lineno)
            result += _pack((0x09 << 24) | (rs_reg << 16) | (rt_reg << 8) | rel8)

        elif mnem == 'ADDI':
            if len(args) != 3:
                raise AsmError(lineno, f"ADDI requires 3 operands, got {len(args)}")
            rd   = _parse_reg(args[0], lineno)
            rs   = _parse_reg(args[1], lineno)
            imm8 = _parse_imm(args[2], lineno, bits=8)
            result += _pack((0x0A << 24) | (rd << 16) | (rs << 8) | imm8)

        # PATCH_AK32_BITWISE_INSTRUCTIONS_V08: AND/OR/XOR are 3-operand R-type
        # (same form as ADD/SUB); NOT is 2-operand (rt slot stays 0).
        elif mnem in ('AND', 'OR', 'XOR'):
            if len(args) != 3:
                raise AsmError(lineno, f"{mnem} requires 3 operands, got {len(args)}")
            rd = _parse_reg(args[0], lineno)
            rs = _parse_reg(args[1], lineno)
            rt = _parse_reg(args[2], lineno)
            result += _pack((_OPCODES[mnem] << 24) | (rd << 16) | (rs << 8) | rt)

        elif mnem == 'NOT':
            if len(args) != 2:
                raise AsmError(lineno, f"NOT requires 2 operands, got {len(args)}")
            rd = _parse_reg(args[0], lineno)
            rs = _parse_reg(args[1], lineno)
            result += _pack((0x0E << 24) | (rd << 16) | (rs << 8))

        else:
            raise AsmError(lineno, f"unknown mnemonic {tokens[0]!r}")

        pc += 4

    return bytes(result), address_map


def assemble(text: str) -> bytes:
    """Assemble *text* and return the binary as bytes.

    Lines starting with or containing ``#`` have the comment stripped.
    Blank lines and label-only lines (``name:``) are skipped silently.
    Raises :class:`AsmError` on any syntax or range error.
    Use :func:`assemble_ex` to also obtain the address map.
    """
    binary, _ = assemble_ex(text)
    return binary
