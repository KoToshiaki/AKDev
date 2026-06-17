# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Concrete simulation devices — RamPart, RomPart, UartPart, InputPart."""
from __future__ import annotations

from core.sim import BusError, Part


# ---------------------------------------------------------------------------
# RamPart — 32-bit little-endian word-addressed RAM
# ---------------------------------------------------------------------------

class RamPart(Part):
    """Byte-array backed RAM.  read/write operate on 32-bit little-endian words.

    The Part stores its own base address so it can compute offsets from raw
    bus addresses (which the Bus passes through unchanged).
    """

    def __init__(self, part_id: str, name: str, size: int, base: int = 0):
        super().__init__(part_id, name)
        if size <= 0:
            raise ValueError(f"size must be > 0, got {size}")
        self.size = size
        self.base = base
        self._mem  = bytearray(size)

    # ---- helpers ----

    def _offset(self, addr: int) -> int:
        off = addr - self.base
        if not (0 <= off <= self.size - 4):
            raise BusError(
                f"{self.id}: address {addr:#010x} out of range "
                f"[{self.base:#010x}, {self.base + self.size - 1:#010x}]"
            )
        return off

    # ---- Part interface ----

    def reset(self) -> None:
        self._mem[:] = bytearray(self.size)

    def read(self, addr: int) -> int:
        off = self._offset(addr)
        return int.from_bytes(self._mem[off:off + 4], "little")

    def write(self, addr: int, value: int) -> None:
        off = self._offset(addr)
        self._mem[off:off + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")

    # ---- bulk helpers ----

    def load_bytes(self, data: bytes, offset: int = 0) -> None:
        """Copy *data* into memory starting at byte *offset*.

        Raises ValueError if the data doesn't fit.
        """
        end = offset + len(data)
        if end > self.size:
            raise ValueError(
                f"load_bytes: data ({len(data)} B) at offset {offset} "
                f"exceeds size {self.size}"
            )
        self._mem[offset:end] = data

    def dump(self) -> bytes:
        """Return the full memory contents as bytes."""
        return bytes(self._mem)


# ---------------------------------------------------------------------------
# RomPart — read-only 32-bit little-endian word-addressed ROM (PATCH_ROM_DEVICE_V08)
# ---------------------------------------------------------------------------

class RomPart(Part):
    """Byte-array backed **read-only** memory.

    Reads behave exactly like :class:`RamPart` (32-bit little-endian words). Writes
    from the CPU / bus (e.g. a stray ``ST``) are silently ignored — a no-op, never
    an error — so a program can't corrupt ROM. The image is set out-of-band via
    :meth:`load_bytes` (IDE / loader / tests) and **survives reset** (unlike RAM,
    which is zeroed): ROM content is the firmware/program, not runtime state.
    """

    def __init__(self, part_id: str, name: str, size: int, base: int = 0):
        super().__init__(part_id, name)
        if size <= 0:
            raise ValueError(f"size must be > 0, got {size}")
        self.size = size
        self.base = base
        self._mem = bytearray(size)

    # ---- helpers ----

    def _offset(self, addr: int) -> int:
        off = addr - self.base
        if not (0 <= off <= self.size - 4):
            raise BusError(
                f"{self.id}: address {addr:#010x} out of range "
                f"[{self.base:#010x}, {self.base + self.size - 1:#010x}]"
            )
        return off

    # ---- Part interface ----

    def reset(self) -> None:
        # Read-only memory keeps its image across reset (RAM clears, ROM does not).
        pass

    def read(self, addr: int) -> int:
        off = self._offset(addr)
        return int.from_bytes(self._mem[off:off + 4], "little")

    def write(self, addr: int, value: int) -> None:
        # Read-only: CPU/bus writes are silently ignored (no exception, no change).
        return None

    # ---- bulk helpers ----

    def load_bytes(self, data: bytes, offset: int = 0) -> None:
        """Set the ROM image (IDE / loader / tests). Raises if *data* doesn't fit."""
        end = offset + len(data)
        if end > self.size:
            raise ValueError(
                f"load_bytes: data ({len(data)} B) at offset {offset} "
                f"exceeds size {self.size}"
            )
        self._mem[offset:end] = data

    def dump(self) -> bytes:
        """Return the full ROM contents as bytes."""
        return bytes(self._mem)


# ---------------------------------------------------------------------------
# UartPart — minimal software UART (TX only for now)
# ---------------------------------------------------------------------------

class UartPart(Part):
    """Minimal UART — collects written bytes as text.

    Register map (relative to base):
      +0  DATA   write: send byte (lower 8 bits) / read: stub (0)
      +4  STATUS read: 0x01 = TX ready (always) / write: no-op
    """

    OFFSET_DATA   = 0
    OFFSET_STATUS = 4
    STATUS_TX_RDY = 0x01

    def __init__(self, part_id: str, name: str, base: int = 0):
        super().__init__(part_id, name)
        self.base = base
        self._buf: list[str] = []

    # ---- Part interface ----

    def reset(self) -> None:
        self._buf.clear()

    def write(self, addr: int, value: int) -> None:
        off = addr - self.base
        if off == self.OFFSET_DATA:
            ch = value & 0xFF
            if ch == 0x0D:              # CR → LF
                self._buf.append("\n")
            elif ch == 0x0A:            # LF
                self._buf.append("\n")
            elif 0x20 <= ch < 0x7F:     # printable ASCII
                self._buf.append(chr(ch))
            # other control characters are silently ignored

    def read(self, addr: int) -> int:
        off = addr - self.base
        if off == self.OFFSET_STATUS:
            return self.STATUS_TX_RDY
        return 0

    # ---- UART-specific helpers ----

    def output_text(self) -> str:
        """Return accumulated TX output as a string."""
        return "".join(self._buf)

    def clear(self) -> None:
        """Discard accumulated TX output."""
        self._buf.clear()


# ---------------------------------------------------------------------------
# InputPart — memory-mapped button/key input (PATCH_INPUT_DEVICE_V08)
# ---------------------------------------------------------------------------

class InputPart(Part):
    """Minimal MMIO input device — readable with the existing ``LD`` instruction.

    Register map (relative to base):
      +0  KEY_STATE  read: currently-held key bitmask / write: no-op
      +4  EDGE_STATE read: keys pressed since last clear / write: CLEAR_EDGE (clears)

    Key bits: 0 up, 1 down, 2 left, 3 right, 4 A, 5 B, 6 Start, 7 Select.
    No ``IN`` instruction is needed: the CPU reads ``bus.read(base)`` via ``LD``.
    Input state is driven from the UI / tests via ``set_keys``.
    """

    OFFSET_KEY  = 0
    OFFSET_EDGE = 4
    _KEY_MASK   = 0xFF

    def __init__(self, part_id: str, name: str, base: int = 0, size: int = 8):
        super().__init__(part_id, name)
        self.base = base
        self.size = size
        self._keys: int = 0   # current held key bitmask
        self._edge: int = 0   # rising-edge bitmask since last clear

    # ---- Part interface ----

    def reset(self) -> None:
        self._keys = 0
        self._edge = 0

    def read(self, addr: int) -> int:
        off = addr - self.base
        if off == self.OFFSET_KEY:
            return self._keys
        if off == self.OFFSET_EDGE:
            return self._edge
        return 0

    def write(self, addr: int, value: int) -> None:
        off = addr - self.base
        if off == self.OFFSET_EDGE:     # CLEAR_EDGE
            self._edge = 0
        # other offsets: no-op (KEY_STATE is read-only)

    # ---- input-specific helpers ----

    def set_keys(self, mask: int) -> None:
        """Set the held-key bitmask; rising edges accumulate into EDGE_STATE."""
        mask &= self._KEY_MASK
        self._edge |= mask & ~self._keys   # newly-pressed bits
        self._keys = mask

    def get_keys(self) -> int:
        """Return the current held-key bitmask."""
        return self._keys

    def clear_edge(self) -> None:
        """Clear the rising-edge bitmask."""
        self._edge = 0
