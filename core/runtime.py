# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Virtual circuit runtime — wraps the AK32 CPU / RAM / UART for stepped, traced execution.

Physically this runs as a normal Python program on the host PC.  Conceptually it
models AKDev's *virtual circuit*: a virtual CPU, virtual RAM and virtual UART whose
state is advanced one instruction at a time (fetch / decode / execute), so each Step
produces a detailed trace of PC, the executed instruction, register changes, memory /
IO accesses and UART output.

The runtime does not create new devices — it wraps the existing bus / ram / uart / cpu
instances so the existing Build / Run paths stay compatible.  See
PATCH_VIRTUAL_CPU_STEP_TRACE_V05.
"""
from __future__ import annotations

from core.cpu import AK32Part


# ---------------------------------------------------------------------------
# Minimal disassembler (NOT a full implementation — covers the 11-instr ISA)
# ---------------------------------------------------------------------------

def disasm(word: int) -> str:
    """Return an ASM-ish string for a raw 32-bit AK32 instruction word.

    Encoding (see core/cpu.py):
        bits 31..24 opcode | 23..16 rd/rs1 | 15..8 rs/rs2 | 7..0 rt/imm8/rel8
    """
    op    = (word >> 24) & 0xFF
    rd    = (word >> 16) & 0xFF
    rs    = (word >>  8) & 0xFF
    imm8  =  word        & 0xFF
    imm16 =  word        & 0xFFFF
    rt    = imm8

    if op == AK32Part.OP_NOP:
        return "NOP"
    if op == AK32Part.OP_HALT:
        return "HALT"
    if op == AK32Part.OP_LDI:
        return f"LDI r{rd}, 0x{imm16:x}"
    if op == AK32Part.OP_OUT:
        return f"OUT [r{rd}], r{rs}"
    if op == AK32Part.OP_ADD:
        return f"ADD r{rd}, r{rs}, r{rt}"
    if op == AK32Part.OP_SUB:
        return f"SUB r{rd}, r{rs}, r{rt}"
    if op == AK32Part.OP_LD:
        return f"LD r{rd}, [r{rs}]"
    if op == AK32Part.OP_ST:
        return f"ST [r{rd}], r{rs}"
    if op == AK32Part.OP_JMP:
        return f"JMP 0x{imm16:x}"
    if op == AK32Part.OP_BEQ:
        rel = imm8 if imm8 < 128 else imm8 - 256
        return f"BEQ r{rd}, r{rs}, {rel}"
    if op == AK32Part.OP_ADDI:
        return f"ADDI r{rd}, r{rs}, {imm8}"
    return f"DW 0x{word:08x}"   # unknown opcode (would halt the CPU)


# ---------------------------------------------------------------------------
# VirtualCircuitRuntime
# ---------------------------------------------------------------------------

class VirtualCircuitRuntime:
    """Stepped, traced execution over an existing bus / ram / uart / cpu.

    The runtime wraps (does not own) the device instances so MainWin's existing
    Build / Run wiring keeps working.  Each ``step()`` advances the virtual CPU by
    one instruction and returns a trace dict; ``run()`` is just repeated ``step()``.
    """

    def __init__(self, bus, ram, uart, cpu):
        self.bus  = bus
        self.ram  = ram
        self.uart = uart
        self.cpu  = cpu
        self.loaded: bool = False
        self.loaded_program: "dict | None" = None
        self.step_count: int = 0
        self.last_trace: "dict | None" = None
        self.trace_history: list[dict] = []

    # ---- program loading ----

    def load_program(self, binary: bytes, *, source_name: str = "",
                     target_node_id: "str | None" = None) -> None:
        """Load *binary* into virtual RAM and reset CPU/UART for execution."""
        self.ram.reset()
        self.ram.load_bytes(binary)
        self.uart.reset()
        self.cpu.reset()
        self.bus.clear_trace()
        self.bus.reset_transactions()
        self.step_count = 0
        self.last_trace = None
        self.trace_history = []
        self.loaded = True
        self.loaded_program = {
            "source_name":    source_name,
            "target_node_id": target_node_id,
            "size":           len(binary),
        }

    def reset(self) -> None:
        """Reset CPU + UART (RAM keeps the loaded program), clear trace state."""
        self.cpu.reset()
        self.uart.reset()
        self.bus.clear_trace()
        self.bus.reset_transactions()
        self.step_count = 0
        self.last_trace = None
        self.trace_history = []

    # ---- execution ----

    def step(self) -> dict:
        """Execute one instruction and return a trace dict.

        If the CPU is already halted, returns a trace with ``halted=True`` and no
        register/memory changes (step_count is not advanced).
        """
        pc_before = self.cpu.pc()
        if self.cpu.halted():
            trace = self._make_trace(
                step=self.step_count, pc_before=pc_before, pc_after=pc_before,
                raw=None, instruction="(halted)", reg_changes={}, memory=[],
                io=[], uart="", halted=True, error=None,
            )
            self.last_trace = trace
            return trace

        regs_before = self.cpu.regs()
        uart_before = self.uart.output_text()

        events: list[tuple] = []
        self.bus.on_access = lambda op, addr, val, pid: events.append((op, addr, val, pid))
        error = None
        try:
            self.cpu.tick()
        except Exception as exc:                     # pragma: no cover - defensive
            error = str(exc)
        finally:
            self.bus.on_access = None

        self.step_count += 1
        pc_after    = self.cpu.pc()
        regs_after  = self.cpu.regs()
        uart_after  = self.uart.output_text()

        # events[0] is the instruction fetch (CPU reads bus.read(pc) first).
        raw = events[0][2] if events else None
        instruction = disasm(raw) if raw is not None else "(no fetch)"

        memory: list[dict] = []
        io:     list[dict] = []
        for idx, (op, addr, val, pid) in enumerate(events):
            if idx == 0:
                continue                              # skip instruction fetch
            if pid == self.uart.id:
                io.append({
                    "type":   op.strip().lower(),
                    "addr":   f"0x{addr:04x}",
                    "value":  f"0x{val:02x}",
                    "device": "UART",
                })
            else:
                memory.append({
                    "type":  op.strip().lower(),
                    "addr":  f"0x{addr:04x}",
                    "value": f"0x{val:08x}",
                })

        reg_changes: dict[str, list[str]] = {}
        for i, (b, a) in enumerate(zip(regs_before, regs_after)):
            if b != a:
                reg_changes[f"r{i}"] = [f"0x{b:08x}", f"0x{a:08x}"]

        trace = self._make_trace(
            step=self.step_count, pc_before=pc_before, pc_after=pc_after,
            raw=raw, instruction=instruction, reg_changes=reg_changes,
            memory=memory, io=io, uart=uart_after[len(uart_before):],
            halted=self.cpu.halted(), error=error,
        )
        self.last_trace = trace
        self.trace_history.append(trace)
        return trace

    def run(self, max_steps: int = 10000) -> list[dict]:
        """Repeatedly ``step()`` until the CPU halts or *max_steps* is reached."""
        traces: list[dict] = []
        for _ in range(max_steps):
            if self.cpu.halted():
                break
            trace = self.step()
            traces.append(trace)
            if trace["halted"]:
                break
        return traces

    # ---- snapshots ----

    def registers(self) -> dict:
        return {
            "pc":         self.cpu.pc(),
            "halted":     self.cpu.halted(),
            "z":          self.cpu.z_flag(),
            "step_count": self.step_count,
            "regs":       self.cpu.regs(),
        }

    def memory_snapshot(self) -> bytes:
        return self.ram.dump()

    def uart_text(self) -> str:
        return self.uart.output_text()

    # ---- helpers ----

    @staticmethod
    def _make_trace(*, step, pc_before, pc_after, raw, instruction, reg_changes,
                    memory, io, uart, halted, error) -> dict:
        return {
            "step":             step,
            "pc_before":        pc_before,
            "pc_after":         pc_after,
            "raw":              raw,
            "instruction":      instruction,
            "register_changes": reg_changes,
            "memory":           memory,
            "io":               io,
            "uart":             uart,
            "halted":           halted,
            "error":            error,
        }
