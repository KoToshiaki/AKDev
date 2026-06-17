# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Device registry (PATCH_DEVICE_REGISTRY_REFACTOR_V08).

Turns a placed part into a *device spec* — a common, runtime/Address-Map-agnostic
descriptor used to build executable devices and the Address Map.  Classification is
**part_id based** (not category based) so ``mem.vram`` is a ``vram`` device and is
never mistaken for ``mem.ram`` (``ram``).

This patch keeps behaviour unchanged: only ``cpu`` / ``ram`` / ``uart`` are
``runtime_backed`` today; other kinds get a spec but no runtime Part.  Multiple
RAM/UART and new-device runtimes are out of scope (see
PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08 / PATCH_DEVICE_EXPANSION_ROM_INPUT_V08).

PATCH_CODE_REGION_MMIO_RELOCATION_V08 adds a ``MemoryLayout`` (named address-space
layouts) that the spec/Address-Map builders consult.  The **default stays the
current behaviour** (``circuit_compat`` / ``legacy``); ``game16`` is defined as a
future candidate only and is never used by default.

Pure / Qt-independent.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryLayout:
    """An address-space layout: where RAM / MMIO / code live in the 16-bit space.

    AK32 is imm16, so every address fits in 64 KB (0x0000–0xFFFF). ``mmio_inside_ram``
    selects whether MMIO windows are carved out of a RAM that spans them (current
    behaviour) or live in a separate, non-overlapping region (future game16-style).
    ``stack_top`` is reserved for a future CALL/RET stack (unused today).
    """
    name: str
    ram_base: int
    ram_size: int
    mmio_base: int
    mmio_stride: int
    mmio_size: int
    mmio_inside_ram: bool
    code_base: int
    reset_pc: int
    stack_top: "int | None" = None


# legacy fixed circuit (no CPU on canvas): 256 B RAM + UART @0x0100 (adjacent).
LEGACY = MemoryLayout(
    name="legacy", ram_base=0x0000, ram_size=0x0100,
    mmio_base=0x0100, mmio_stride=0x10, mmio_size=0x08, mmio_inside_ram=False,
    code_base=0x0000, reset_pc=0x0000,
)

# circuit mode (default): RAM fills the 64 KB space, UART is an MMIO overlay window.
CIRCUIT_COMPAT = MemoryLayout(
    name="circuit_compat", ram_base=0x0000, ram_size=0x10000,
    mmio_base=0x0100, mmio_stride=0x10, mmio_size=0x08, mmio_inside_ram=True,
    code_base=0x0000, reset_pc=0x0000,
)

# game16 (DESIGN-ONLY candidate — never used by default this patch). Non-overlapping
# regions: ROM 0x0000–0x7FFF / RAM 0x8000–0xBFFF / VRAM 0xC000–0xDFFF (placed by
# future device expansion) / MMIO 0xE000 / reserved 0xF000–0xFFFF.
GAME16 = MemoryLayout(
    name="game16", ram_base=0x8000, ram_size=0x4000,
    mmio_base=0xE000, mmio_stride=0x10, mmio_size=0x08, mmio_inside_ram=False,
    code_base=0x0000, reset_pc=0x0000, stack_top=0xBFFF,
)

_LAYOUTS = {"legacy": LEGACY, "circuit": CIRCUIT_COMPAT,
            "circuit_compat": CIRCUIT_COMPAT, "game16": GAME16}


def get_memory_layout(mode: "str | None" = None) -> MemoryLayout:
    """Return a named MemoryLayout. Default / unknown -> ``circuit_compat``.

    ``None`` / ``"circuit"`` / ``"circuit_compat"`` -> circuit_compat; ``"legacy"`` ->
    legacy; ``"game16"`` -> game16. An unknown name safely falls back to
    circuit_compat (the current default) rather than raising.
    """
    if mode is None:
        return CIRCUIT_COMPAT
    return _LAYOUTS.get(mode, CIRCUIT_COMPAT)


# Canonical memory-map constants (mirrored by ui.win which imports them). Derived
# from the layouts so there is a single source; values are unchanged.
RAM_BASE         = CIRCUIT_COMPAT.ram_base    # 0x0000
UART_BASE        = CIRCUIT_COMPAT.mmio_base   # 0x0100
UART_SIZE        = CIRCUIT_COMPAT.mmio_size   # 0x0008
CIRCUIT_RAM_SIZE = CIRCUIT_COMPAT.ram_size    # 0x10000 (64 KB)
LEGACY_RAM_SIZE  = LEGACY.ram_size            # 0x0100 (256 bytes)

# part_id -> device kind (the single source of truth; category is only a fallback).
_KIND_BY_PART_ID = {
    "cpu.ak32":      "cpu",
    "mem.ram":       "ram",
    "mem.vram":      "vram",
    "io.uart":       "uart",
    "io.gpio":       "gpio",
    "io.timer":      "timer",
    "video.regs":    "video_regs",
    "video.out":     "video_out",
    "bus.bridge":    "bridge",
    "fpga.generic":  "fpga",
    "fpga.ecp5_85f": "fpga",
}

# kind -> address-space role.
_ROLE_BY_KIND = {
    "cpu":        "cpu",
    "ram":        "memory",
    "vram":       "memory",
    "rom":        "memory",
    "uart":       "mmio",
    "gpio":       "mmio",
    "timer":      "mmio",
    "video_regs": "mmio",
    "video_out":  "none",
    "bridge":     "none",
    "fpga":       "none",
    "unsupported": "none",
}

# kinds that have a runtime Part *today* (behaviour-preserving scope of this patch).
_RUNTIME_BACKED = {"cpu", "ram", "uart"}

# stable runtime ids (must not change — bus tracing / signal overlay / tests).
_RUNTIME_ID = {"cpu": "sim_cpu", "ram": "sim_ram", "uart": "sim_uart"}

_LABEL_BY_KIND = {
    "cpu": "CPU", "ram": "RAM", "vram": "VRAM", "rom": "ROM", "uart": "UART",
    "gpio": "GPIO", "timer": "TIMER", "video_regs": "VIDEO", "video_out": "VIDEO",
    "bridge": "BRIDGE", "fpga": "FPGA", "unsupported": "DEVICE",
}

_MEMORY_KINDS = ("ram", "vram", "rom")


def device_kind(part: "dict | None") -> str:
    """Classify a part into a device kind by ``part_id`` (category fallback).

    Unknown / missing parts return ``"unsupported"``. Notably ``mem.vram`` -> ``vram``
    (never ``ram``), so a VRAM is never mistaken for RAM.
    """
    if not isinstance(part, dict):
        return "unsupported"
    pid = part.get("id")
    if pid in _KIND_BY_PART_ID:
        return _KIND_BY_PART_ID[pid]
    # Conservative category fallback: only CPU is safe to infer. A mem/io part with
    # an unknown id is NOT assumed to be ram/uart (avoids VRAM-style misclassification).
    if part.get("category") == "cpu":
        return "cpu"
    return "unsupported"


def device_role(kind: str) -> str:
    """Return the address-space role for a device kind (memory/mmio/io/cpu/none)."""
    return _ROLE_BY_KIND.get(kind, "none")


def is_addressable_kind(kind: str) -> bool:
    """True if the kind occupies bus address space (memory / mmio)."""
    return device_role(kind) in ("memory", "mmio")


def is_runtime_backed_kind(kind: str) -> bool:
    """True if a runtime Part exists for this kind today (cpu/ram/uart)."""
    return kind in _RUNTIME_BACKED


def _base_size(kind: str, layout: MemoryLayout):
    if kind == "ram":
        return layout.ram_base, layout.ram_size
    if kind == "uart":
        return layout.mmio_base, layout.mmio_size
    return None, None


def _spec(node_id, part, kind, layout: MemoryLayout) -> dict:
    base, size = _base_size(kind, layout)
    end = (base + size - 1) if (base is not None and size) else None
    return {
        "node_id":        node_id,
        "part_id":        (part or {}).get("id"),
        "category":       (part or {}).get("category"),
        "kind":           kind,
        "role":           device_role(kind),
        "addressable":    is_addressable_kind(kind),
        "runtime_backed": is_runtime_backed_kind(kind),
        "runtime_id":     _RUNTIME_ID.get(kind),
        "label":          _LABEL_BY_KIND.get(kind, kind.upper()),
        "base":           base,
        "size":           size,
        "end":            end,
        "attach_ranges":  [(base, end)] if end is not None else [],
        "reserved":       [],
        "overlay":        None,
        "part":           part,
    }


def make_device_spec(node_id: "str | None", part: "dict | None",
                     *, mode: str = "circuit",
                     layout: "MemoryLayout | None" = None) -> dict:
    """Build a device spec for a placed node + part.

    Intrinsic fields (kind/role/addressable/runtime_backed/runtime_id/base/size) are
    set here; base/size come from the *layout* (defaults to the layout for *mode* —
    circuit_compat / legacy, i.e. current values). The Address Map's carved
    ``attach_ranges`` are computed later by
    ``core.circuit.build_address_map_from_devices`` once all devices are known.
    """
    layout = layout or get_memory_layout(mode)
    return _spec(node_id, part, device_kind(part), layout)


def synthetic_spec(kind: str, *, mode: str = "circuit",
                   node_id: "str | None" = None,
                   layout: "MemoryLayout | None" = None) -> dict:
    """A spec for the fixed/legacy circuit where no canvas part exists."""
    layout = layout or get_memory_layout(mode)
    return _spec(node_id, None, kind, layout)


def legacy_device_specs(layout: "MemoryLayout | None" = None) -> list:
    """The fixed legacy circuit (no CPU on canvas): CPU + 256B RAM + UART @0x0100."""
    layout = layout or LEGACY
    return [synthetic_spec("cpu", node_id=None, layout=layout),
            synthetic_spec("ram", node_id=None, layout=layout),
            synthetic_spec("uart", node_id=None, layout=layout)]


def build_device_specs(nodes: list, *, mode: str = "circuit",
                       layout: "MemoryLayout | None" = None) -> list:
    """Build device specs for a list of ``{"node_id", "part"}`` entries."""
    layout = layout or get_memory_layout(mode)
    return [make_device_spec(n.get("node_id"), n.get("part"), layout=layout)
            for n in (nodes or [])]


# ---------------------------------------------------------------------------
# Multiple MMIO / RAM handling (PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08)
# ---------------------------------------------------------------------------

MULTI_RAM_UNSUPPORTED = "MULTI_RAM_UNSUPPORTED"


def assign_mmio_bases(specs: list, *, layout: "MemoryLayout | None" = None) -> list:
    """Auto-place MMIO windows (UART etc.) for an Address Map. Returns new specs.

    The **first** MMIO device keeps the canonical UART window
    (``layout.mmio_base``, ``layout.mmio_size``) and stays runtime-backed
    (``runtime_id`` ``sim_uart``). Subsequent MMIO devices are placed at
    ``mmio_base + n*mmio_stride`` (default 0x0110, 0x0120 …); they are Address-Map
    placed / diagnosed only and are **not** runtime-backed in this patch (so a
    single UART is unchanged). Memory / CPU specs are returned unchanged. Default
    layout (circuit_compat) reproduces the current 0x0100 / 0x0110 placement.
    """
    layout = layout or get_memory_layout()
    out: list = []
    n = 0
    for s in specs:
        s = dict(s)
        if s.get("addressable") and s.get("role") == "mmio":
            base = layout.mmio_base + n * layout.mmio_stride
            s["base"] = base
            s["size"] = layout.mmio_size
            s["end"]  = base + layout.mmio_size - 1
            s["attach_ranges"] = [(base, s["end"])]
            if n > 0:
                # extra MMIO windows are placed/diagnosed only (no runtime Part yet)
                s["runtime_backed"] = False
                s["runtime_id"]     = None
                s["device_id"]      = f"mmio_{s.get('node_id') or n}"
            n += 1
        out.append(s)
    return out


def parse_address_int(text) -> int:
    """Parse an address/size value from UI text (PATCH_ADDRESS_MAP_EDITOR_V08).

    Accepts an int as-is, ``0x``-prefixed hex (``0x0100``), or plain decimal
    (``256``; leading zeros tolerated). Raises ``ValueError`` on anything else.
    """
    if isinstance(text, bool):
        raise ValueError("invalid address value")
    if isinstance(text, int):
        return text
    t = str(text).strip().lower()
    if not t:
        raise ValueError("empty address value")
    if t.startswith("0x") or t.startswith("-0x"):
        return int(t, 16)
    return int(t, 10)


def apply_address_overrides(specs: list, overrides: "dict | None") -> list:
    """Return new specs with manual base/size overrides applied (pure; non-mutating).

    ``overrides`` maps ``node_id`` -> ``{"mode": "auto"|"manual", "base", "size"}``.
    Only ``mode == "manual"`` entries on **addressable** specs override ``base`` /
    ``size`` (and recompute ``end`` / ``attach_ranges``). Empty / None -> the specs
    are returned unchanged (a no-op copy), so the default pipeline is identical.
    """
    out: list = []
    overrides = overrides or {}
    for s in specs:
        s = dict(s)
        ov = overrides.get(s.get("node_id"))
        if (ov and ov.get("mode") == "manual" and s.get("addressable")
                and ov.get("base") is not None and ov.get("size") is not None):
            base, size = ov["base"], ov["size"]
            s["base"] = base
            s["size"] = size
            s["end"]  = base + size - 1
            s["attach_ranges"] = [(base, base + size - 1)]
        out.append(s)
    return out


def multi_device_warnings(specs: list) -> list:
    """Warn (issue dicts) about device configurations not fully supported yet.

    Currently: more than one RAM. Only the first RAM is runtime-backed and
    address-mapped (16-bit / 64 KB space — true multi-RAM co-location needs RAM
    resizing / MMIO relocation, deferred to later patches). Issue shape matches
    core.port_validation / core.bus_validation.
    """
    issues: list = []
    rams = [s for s in (specs or []) if s.get("kind") == "ram"]
    if len(rams) > 1:
        issues.append({
            "severity": "warning",
            "code": MULTI_RAM_UNSUPPORTED,
            "message": (f"Multiple RAM devices ({len(rams)}); only the first is "
                        f"runtime-backed and address-mapped"),
            "nodes": [s.get("node_id") for s in rams],
            "details": {"unsupported": [s.get("node_id") for s in rams[1:]]},
        })
    return issues
