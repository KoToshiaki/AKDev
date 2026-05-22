# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AK32 minimal assembler — NOP / HALT / LDI / OUT.

Instruction encoding (32-bit fixed length, little-endian output)
-----------------------------------------------------------------
bits 31..24  opcode
bits 23..16  rd / ra  (destination or address register)
bits 15..8   rs        (source register)   [LDI: imm16 high byte]
bits  7..0   imm8                          [LDI: imm16 low byte]

Opcodes: NOP=0x00  HALT=0x01  LDI=0x02  OUT=0x03
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


# ---------------------------------------------------------------------------
# Two-pass assembler
# ---------------------------------------------------------------------------

_OPCODES = {'NOP': 0x00, 'HALT': 0x01, 'LDI': 0x02, 'OUT': 0x03}


def assemble(text: str) -> bytes:
    """Assemble *text* and return the binary as bytes.

    Lines starting with or containing ``#`` have the comment stripped.
    Blank lines and label-only lines (``name:``) are skipped silently.
    Raises :class:`AsmError` on any syntax or range error.
    """
    lines = text.splitlines()

    # ------------------------------------------------------------------
    # Pass 1 — collect labels, compute their byte addresses
    # ------------------------------------------------------------------
    labels: dict[str, int] = {}
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
            pc += 4

    # ------------------------------------------------------------------
    # Pass 2 — encode instructions
    # ------------------------------------------------------------------
    result = bytearray()
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

        else:
            raise AsmError(lineno, f"unknown mnemonic {tokens[0]!r}")

    return bytes(result)
