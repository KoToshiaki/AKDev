# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AK32 minimal CPU emulator — NOP / HALT / LDI / OUT."""
from __future__ import annotations

from core.sim import BusError, Bus, Part


class AK32Part(Part):
    """Minimal AK32 CPU.

    32-bit fixed-length instruction encoding
    ----------------------------------------
    bits 31..24  opcode
    bits 23..16  rd / ra  (destination or address register index)
    bits 15..8   rs        (source register index)      [LDI: imm16 high byte]
    bits  7..0   imm8                                   [LDI: imm16 low byte]

    Opcodes
    -------
    0x00  NOP
    0x01  HALT
    0x02  LDI  rd, imm16   — load 16-bit zero-extended immediate into rd
    0x03  OUT  [rd], rs    — bus.write(regs[rd], regs[rs])

    r0 is hardwired to 0 and cannot be written.
    """

    OP_NOP  = 0x00
    OP_HALT = 0x01
    OP_LDI  = 0x02
    OP_OUT  = 0x03

    _NREGS = 16

    def __init__(self, part_id: str, name: str, bus: Bus, reset_pc: int = 0):
        super().__init__(part_id, name)
        self._bus      = bus
        self._reset_pc = reset_pc
        self._regs:   list[int] = [0] * self._NREGS
        self._pc:     int       = reset_pc
        self._z:      bool      = False
        self._halted: bool      = False

    # ---- Part interface ----

    def reset(self) -> None:
        self._regs   = [0] * self._NREGS
        self._pc     = self._reset_pc
        self._z      = False
        self._halted = False

    def tick(self) -> None:
        if self._halted:
            return
        instr    = self._bus.read(self._pc)
        self._pc += 4
        self._execute(instr)

    # ---- CPU-specific accessors ----

    def regs(self) -> list[int]:
        return list(self._regs)

    def pc(self) -> int:
        return self._pc

    def z_flag(self) -> bool:
        return self._z

    def halted(self) -> bool:
        return self._halted

    # ---- internals ----

    def _set_reg(self, idx: int, value: int) -> None:
        if idx == 0:
            return          # r0 is hardwired to 0
        self._regs[idx] = value & 0xFFFFFFFF

    def _execute(self, instr: int) -> None:
        op    = (instr >> 24) & 0xFF
        rd    = (instr >> 16) & 0xFF
        rs    = (instr >>  8) & 0xFF
        imm16 =  instr        & 0xFFFF

        if op == self.OP_NOP:
            pass

        elif op == self.OP_HALT:
            self._halted = True
            self._pc -= 4           # keep PC pointing at HALT

        elif op == self.OP_LDI:
            self._set_reg(rd, imm16)
            self._z = (imm16 == 0)

        elif op == self.OP_OUT:
            addr  = self._regs[rd]
            value = self._regs[rs]
            try:
                self._bus.write(addr, value)
            except BusError:
                self._halted = True

        else:
            self._halted = True     # unknown opcode → halt
