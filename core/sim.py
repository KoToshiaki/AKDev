# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Core simulator — Part, Port, Bus, Chip, Sim."""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Port
# ---------------------------------------------------------------------------

class Port:
    """A named, typed connection point on a Part."""

    def __init__(self, name: str, type: str, direction: str = "inout"):
        self.name      = name
        self.type      = type      # e.g. "bus.master", "clock", "irq"
        self.direction = direction # "in" | "out" | "inout"

    def __repr__(self) -> str:
        return f"Port({self.name!r}, {self.type!r}, {self.direction!r})"


# ---------------------------------------------------------------------------
# Part — base class for all simulation parts
# ---------------------------------------------------------------------------

class Part:
    """Abstract simulation part.  Subclass and override reset/tick/read/write."""

    def __init__(self, part_id: str, name: str):
        self.id    = part_id
        self.name  = name
        self.ports: list[Port] = []

    # ---- lifecycle ----

    def reset(self) -> None:
        """Reset internal state to power-on defaults."""

    def tick(self) -> None:
        """Advance one simulation cycle."""

    # ---- bus interface ----

    def read(self, addr: int) -> int:
        """Return the value at *addr* (raw bus address).  Default: 0."""
        return 0

    def write(self, addr: int, value: int) -> None:
        """Write *value* to *addr* (raw bus address).  Default: no-op."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r}, name={self.name!r})"


# ---------------------------------------------------------------------------
# Bus — address-mapped routing to Parts
# ---------------------------------------------------------------------------

class BusError(Exception):
    """Raised for unmapped addresses or overlapping registrations."""


class Bus:
    """Simple flat address bus.  Parts are registered with a base address and
    size; read/write are dispatched to the matching Part.

    Optional tracing: set tracing=True to record every read/write.
    Pass cycle_fn=lambda: <int> to include cycle numbers in trace entries.
    """

    def __init__(self, name: str = "bus", cycle_fn=None):
        self.name              = name
        self.tracing           = False
        self.last_transactions: dict = {}   # {part_id: ("READ"|"WRITE", addr, val)}
        self._map:   list[tuple[int, int, Part]] = []
        self._trace: list[str]                   = []
        self._cycle_fn = cycle_fn  # optional callable -> int

    # ---- registration ----

    def attach(self, part: Part, base: int, size: int) -> None:
        """Register *part* at address range [base, base+size).

        Raises BusError on overlap.
        """
        end = base + size - 1
        for b, e, existing in self._map:
            if not (end < b or base > e):
                raise BusError(
                    f"Address overlap: [{base:#010x}, {end:#010x}] "
                    f"conflicts with {existing.id!r} [{b:#010x}, {e:#010x}]"
                )
        self._map.append((base, end, part))

    # ---- routing ----

    def _lookup(self, addr: int) -> Part:
        for base, end, part in self._map:
            if base <= addr <= end:
                return part
        raise BusError(f"No device mapped at address {addr:#010x}")

    def read(self, addr: int) -> int:
        part  = self._lookup(addr)
        value = part.read(addr)
        self.last_transactions[part.id] = ("READ", addr, value)
        if self.tracing:
            self._trace.append(self._fmt("READ ", addr, value, part.id))
        return value

    def write(self, addr: int, value: int) -> None:
        part = self._lookup(addr)
        part.write(addr, value)
        self.last_transactions[part.id] = ("WRITE", addr, value)
        if self.tracing:
            self._trace.append(self._fmt("WRITE", addr, value, part.id))

    # ---- trace helpers ----

    def _fmt(self, op: str, addr: int, value: int, part_id: str) -> str:
        prefix = f"[{self._cycle_fn()}] " if self._cycle_fn else ""
        return (
            f"{prefix}{op} addr={addr:#06x}  val={value:#010x}  part={part_id}"
        )

    def reset_transactions(self) -> None:
        """Clear the last_transactions snapshot."""
        self.last_transactions.clear()

    def clear_trace(self) -> None:
        """Discard all accumulated trace entries."""
        self._trace.clear()

    def get_trace(self) -> list[str]:
        """Return a snapshot of accumulated trace entries."""
        return list(self._trace)

    def __repr__(self) -> str:
        return f"Bus({self.name!r}, {len(self._map)} device(s))"


# ---------------------------------------------------------------------------
# Chip — a group of Parts sharing a Bus
# ---------------------------------------------------------------------------

class Chip:
    """One physical FPGA / MCU that contains multiple Parts on a shared Bus."""

    def __init__(self, chip_id: str, name: str = ""):
        self.id    = chip_id
        self.name  = name or chip_id
        self.parts: list[Part] = []
        self.bus   = Bus(f"{chip_id}.bus")

    def add_part(self, part: Part, base: int = 0, size: int = 0) -> None:
        """Add *part* to the chip.  If size > 0, also attaches it to the bus."""
        self.parts.append(part)
        if size > 0:
            self.bus.attach(part, base, size)

    def reset(self) -> None:
        for part in self.parts:
            part.reset()

    def tick(self) -> None:
        for part in self.parts:
            part.tick()

    def __repr__(self) -> str:
        return f"Chip({self.id!r}, {len(self.parts)} part(s))"


# ---------------------------------------------------------------------------
# Sim — top-level simulation controller
# ---------------------------------------------------------------------------

class Sim:
    """Simulation controller.  Owns Chips, drives reset/step, and keeps a log."""

    def __init__(self):
        self.chips: list[Chip] = []
        self.cycle: int        = 0
        self.log:   list[str]  = []

    # ---- configuration ----

    def add_chip(self, chip: Chip) -> None:
        self.chips.append(chip)

    # ---- control ----

    def reset(self) -> None:
        """Reset cycle counter and call reset() on every Part in every Chip."""
        self.cycle = 0
        for chip in self.chips:
            chip.reset()
        self._emit("RESET")

    def step(self) -> None:
        """Advance all chips by one cycle."""
        for chip in self.chips:
            chip.tick()
        self.cycle += 1

    def run_steps(self, n: int) -> None:
        """Advance *n* cycles."""
        for _ in range(n):
            self.step()

    # ---- log ----

    def _emit(self, msg: str) -> None:
        self.log.append(f"[{self.cycle}] {msg}")

    def clear_log(self) -> None:
        self.log.clear()

    def __repr__(self) -> str:
        return f"Sim(cycle={self.cycle}, chips={len(self.chips)})"
