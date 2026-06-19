# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""AK32 CPU emulator — NOP / HALT / LDI / OUT / ADD / SUB / LD / ST / JMP / BEQ / ADDI / AND / OR / XOR / NOT."""
from __future__ import annotations

from core.sim import BusError, Bus, Part


class AK32Part(Part):
    """AK32 CPU with 15-instruction ISA.

    32-bit fixed-length instruction encoding
    ----------------------------------------
    bits 31..24  opcode
    bits 23..16  rd / rs  (destination or compare reg 1)
    bits 15..8   rs / rt  (source reg or compare reg 2)
    bits  7..0   rt / imm8 / rel8

    Opcodes
    -------
    0x00  NOP
    0x01  HALT
    0x02  LDI  rd, imm16   — regs[rd] = zero-extend(imm16)
    0x03  OUT  [rd], rs    — bus.write(regs[rd], regs[rs])
    0x04  ADD  rd, rs, rt  — regs[rd] = regs[rs] + regs[rt]
    0x05  SUB  rd, rs, rt  — regs[rd] = regs[rs] - regs[rt]
    0x06  LD   rd, [rs]    — regs[rd] = bus.read(regs[rs])
    0x07  ST   [rd], rs    — bus.write(regs[rd], regs[rs])
    0x08  JMP  imm16       — pc = imm16
    0x09  BEQ  rs, rt, rel8 — if regs[rs]==regs[rt]: pc += signed(rel8)*4
    0x0A  ADDI rd, rs, imm8 — regs[rd] = regs[rs] + imm8
    0x0B  AND  rd, rs, rt  — regs[rd] = regs[rs] & regs[rt]   (PATCH_AK32_BITWISE_INSTRUCTIONS_V08)
    0x0C  OR   rd, rs, rt  — regs[rd] = regs[rs] | regs[rt]
    0x0D  XOR  rd, rs, rt  — regs[rd] = regs[rs] ^ regs[rt]
    0x0E  NOT  rd, rs      — regs[rd] = ~regs[rs] (32-bit)

    r0 is hardwired to 0 and cannot be written.
    Z flag is updated by LDI, ADD, SUB, LD, ADDI, AND, OR, XOR, NOT (result == 0).
    BEQ does not update Z; it compares rs==rt internally.
    """

    OP_NOP  = 0x00
    OP_HALT = 0x01
    OP_LDI  = 0x02
    OP_OUT  = 0x03
    OP_ADD  = 0x04
    OP_SUB  = 0x05
    OP_LD   = 0x06
    OP_ST   = 0x07
    OP_JMP  = 0x08
    OP_BEQ  = 0x09
    OP_ADDI = 0x0A
    OP_AND  = 0x0B          # PATCH_AK32_BITWISE_INSTRUCTIONS_V08
    OP_OR   = 0x0C
    OP_XOR  = 0x0D
    OP_NOT  = 0x0E

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
        imm8  =  instr        & 0xFF
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

        elif op == self.OP_ADD:
            rt     = imm8
            result = self._regs[rs] + self._regs[rt]
            self._set_reg(rd, result)
            self._z = ((result & 0xFFFFFFFF) == 0)

        elif op == self.OP_SUB:
            rt     = imm8
            result = self._regs[rs] - self._regs[rt]
            self._set_reg(rd, result)
            self._z = ((result & 0xFFFFFFFF) == 0)

        elif op == self.OP_LD:
            addr = self._regs[rs]
            try:
                value = self._bus.read(addr)
            except BusError:
                self._halted = True
                return
            self._set_reg(rd, value)
            self._z = ((value & 0xFFFFFFFF) == 0)

        elif op == self.OP_ST:
            addr  = self._regs[rd]
            value = self._regs[rs]
            try:
                self._bus.write(addr, value)
            except BusError:
                self._halted = True

        elif op == self.OP_JMP:
            self._pc = imm16

        elif op == self.OP_BEQ:
            # rs1 = bits 23:16 (rd slot), rs2 = bits 15:8 (rs slot), rel8 = imm8
            rs1  = rd
            rs2  = rs
            rel8 = imm8 if imm8 < 128 else imm8 - 256  # signed 8-bit
            if self._regs[rs1] == self._regs[rs2]:
                self._pc += rel8 * 4

        elif op == self.OP_ADDI:
            result = self._regs[rs] + imm8
            self._set_reg(rd, result)
            self._z = ((result & 0xFFFFFFFF) == 0)

        elif op == self.OP_AND:
            rt     = imm8
            result = self._regs[rs] & self._regs[rt]
            self._set_reg(rd, result)
            self._z = ((result & 0xFFFFFFFF) == 0)

        elif op == self.OP_OR:
            rt     = imm8
            result = self._regs[rs] | self._regs[rt]
            self._set_reg(rd, result)
            self._z = ((result & 0xFFFFFFFF) == 0)

        elif op == self.OP_XOR:
            rt     = imm8
            result = self._regs[rs] ^ self._regs[rt]
            self._set_reg(rd, result)
            self._z = ((result & 0xFFFFFFFF) == 0)

        elif op == self.OP_NOT:
            result = (~self._regs[rs]) & 0xFFFFFFFF
            self._set_reg(rd, result)
            self._z = (result == 0)

        else:
            self._halted = True     # unknown opcode → halt
