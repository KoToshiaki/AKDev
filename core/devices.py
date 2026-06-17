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

Pure / Qt-independent.
"""
from __future__ import annotations

# Canonical memory-map constants (mirrored by ui.win which imports them).
RAM_BASE         = 0x0000
UART_BASE        = 0x0100
UART_SIZE        = 0x0008
CIRCUIT_RAM_SIZE = 0x10000   # circuit mode: RAM fills the 16-bit space (64 KB)
LEGACY_RAM_SIZE  = 0x0100    # legacy fixed circuit: 256 bytes

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


def _base_size(kind: str, mode: str):
    if kind == "ram":
        return RAM_BASE, (CIRCUIT_RAM_SIZE if mode == "circuit" else LEGACY_RAM_SIZE)
    if kind == "uart":
        return UART_BASE, UART_SIZE
    return None, None


def make_device_spec(node_id: "str | None", part: "dict | None",
                     *, mode: str = "circuit") -> dict:
    """Build a device spec for a placed node + part.

    Intrinsic fields (kind/role/addressable/runtime_backed/runtime_id/base/size) are
    set here; the Address Map's carved ``attach_ranges`` are computed later by
    ``core.circuit.build_address_map_from_devices`` once all devices are known.
    """
    kind        = device_kind(part)
    base, size  = _base_size(kind, mode)
    end         = (base + size - 1) if (base is not None and size) else None
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


def synthetic_spec(kind: str, *, mode: str = "circuit",
                   node_id: "str | None" = None) -> dict:
    """A spec for the fixed/legacy circuit where no canvas part exists."""
    base, size = _base_size(kind, mode)
    end = (base + size - 1) if (base is not None and size) else None
    return {
        "node_id":        node_id,
        "part_id":        None,
        "category":       None,
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
        "part":           None,
    }


def legacy_device_specs() -> list:
    """The fixed legacy circuit (no CPU on canvas): CPU + 256B RAM + UART @0x0100."""
    return [synthetic_spec("cpu", mode="legacy"),
            synthetic_spec("ram", mode="legacy"),
            synthetic_spec("uart", mode="legacy")]


def build_device_specs(nodes: list, *, mode: str = "circuit") -> list:
    """Build device specs for a list of ``{"node_id", "part"}`` entries."""
    return [make_device_spec(n.get("node_id"), n.get("part"), mode=mode)
            for n in (nodes or [])]


# ---------------------------------------------------------------------------
# Multiple MMIO / RAM handling (PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08)
# ---------------------------------------------------------------------------

MULTI_RAM_UNSUPPORTED = "MULTI_RAM_UNSUPPORTED"


def assign_mmio_bases(specs: list) -> list:
    """Auto-place MMIO windows (UART etc.) for an Address Map. Returns new specs.

    The **first** MMIO device keeps the canonical UART window (``0x0100``, 8 B) and
    stays runtime-backed (``runtime_id`` ``sim_uart``). Subsequent MMIO devices are
    placed at ``0x0110``, ``0x0120`` … (16-byte stride, 8-byte size); they are
    Address-Map placed / diagnosed only and are **not** runtime-backed in this patch
    (so a single UART is unchanged). Memory / CPU specs are returned unchanged.
    """
    out: list = []
    n = 0
    for s in specs:
        s = dict(s)
        if s.get("addressable") and s.get("role") == "mmio":
            base = UART_BASE + n * 0x10
            s["base"] = base
            s["size"] = UART_SIZE
            s["end"]  = base + UART_SIZE - 1
            s["attach_ranges"] = [(base, s["end"])]
            if n > 0:
                # extra MMIO windows are placed/diagnosed only (no runtime Part yet)
                s["runtime_backed"] = False
                s["runtime_id"]     = None
                s["device_id"]      = f"mmio_{s.get('node_id') or n}"
            n += 1
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
