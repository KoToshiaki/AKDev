# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Circuit resolver — derive an executable circuit plan from a Canvas topology.

AKDev's goal is to execute the circuit the user draws on the Canvas, not a fixed
internal CPU/RAM/UART.  This module turns the placed parts and their wire
connections into a minimal *CircuitPlan*: which CPU runs, which RAM/UART are wired
to it, and what (if anything) is wrong with the wiring.

The minimal target is a single CPU + RAM + UART.  Address maps, multiple CPUs and
strict bus protocols are out of scope here (see PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05).
"""
from __future__ import annotations

from core.devices import device_kind


def _node_kind(node: dict) -> str:
    """Classify a CircuitPlan node by device kind (part_id based, category fallback).

    PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08: role detection moved off raw ``category``
    onto ``core.devices.device_kind`` so e.g. ``mem.vram`` (kind ``vram``) is NOT
    treated as RAM.
    """
    return device_kind({"id": node.get("part_id"), "category": node.get("category")})


def _is_cpu(node: dict) -> bool:
    return _node_kind(node) == "cpu"


def _is_ram(node: dict) -> bool:
    return _node_kind(node) == "ram"


def _is_uart(node: dict) -> bool:
    return _node_kind(node) == "uart"


def resolve_circuit(nodes: list[dict], connections: list[dict],
                    target_cpu_id: "str | None" = None) -> dict:
    """Resolve a CircuitPlan from canvas *nodes* and *connections*.

    nodes:        [{"node_id", "category", "part_id", "name"}]
    connections:  [{"from_node", "to_node"}]  (treated as undirected adjacency)
    target_cpu_id: the currently selected node id, used to pick the execution CPU
                   when several CPUs are placed (PATCH_TARGET_CPU_SELECTION_V07).

    Returns a dict::

        {
          "ok": bool,                 # True only when the circuit can execute
          "issues": [str],            # human-readable problems (empty when ok)
          "cpu": node_id | None,      # the CPU that will run (== target_cpu)
          "target_cpu": node_id | None,  # execution target CPU
          "rams": [node_id],          # RAM parts wired to the target CPU
          "uarts": [node_id],         # UART parts wired to the target CPU
          "cpu_present": bool,        # any CPU placed at all (circuit-mode flag)
        }

    Target CPU rules:
      * 0 CPUs   -> legacy (cpu/target_cpu None, cpu_present False).
      * 1 CPU    -> that CPU is the target (selection is ignored).
      * N CPUs   -> the selected CPU (``target_cpu_id``) is the target; only its
                    connectivity is checked. If nothing valid is selected the
                    circuit is *ambiguous* and blocked.
    """
    cpus  = [n for n in nodes if _is_cpu(n)]
    rams  = [n for n in nodes if _is_ram(n)]
    uarts = [n for n in nodes if _is_uart(n)]

    # Undirected adjacency between node ids.
    adj: set[frozenset] = set()
    for c in connections:
        a = c.get("from_node")
        b = c.get("to_node")
        if a and b and a != b:
            adj.add(frozenset((a, b)))

    def wired(x: str, y: str) -> bool:
        return frozenset((x, y)) in adj

    cpu_present = len(cpus) > 0
    cpu_ids = [c["node_id"] for c in cpus]

    if len(cpus) == 0:
        return {
            "ok": False, "issues": ["no CPU part on canvas"],
            "cpu": None, "target_cpu": None,
            "rams": [], "uarts": [], "cpu_present": False,
        }

    # Pick the target CPU. A single CPU is always the target (selection-free); with
    # several CPUs the selected one decides, otherwise the circuit is ambiguous.
    if len(cpus) == 1:
        target = cpu_ids[0]
    elif target_cpu_id is not None and target_cpu_id in cpu_ids:
        target = target_cpu_id
    else:
        return {
            "ok": False,
            "issues": [f"multiple CPU parts ({len(cpus)}). Select one CPU to run."],
            "cpu": None, "target_cpu": None,
            "rams": [], "uarts": [], "cpu_present": True,
        }

    # Only the target CPU's connectivity matters — an unconnected non-target CPU
    # must not block the target's execution. Sort by node id so the "first" RAM/UART
    # is deterministic (earliest-placed = primary; PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08)
    # regardless of canvas scene ordering.
    conn_rams  = sorted(r["node_id"] for r in rams  if wired(target, r["node_id"]))
    conn_uarts = sorted(u["node_id"] for u in uarts if wired(target, u["node_id"]))

    issues: list[str] = []
    if not rams:
        issues.append("no RAM part on canvas")
    elif not conn_rams:
        issues.append(f"target CPU {target} has no connected RAM")

    if not uarts:
        issues.append("no UART part on canvas")
    elif not conn_uarts:
        issues.append(f"target CPU {target} has no connected UART")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "cpu": target,
        "target_cpu": target,
        "rams": conn_rams,
        "uarts": conn_uarts,
        "cpu_present": cpu_present,
    }


# ---------------------------------------------------------------------------
# Address map (PATCH_ADDRESS_MAP_V07)
# ---------------------------------------------------------------------------
#
# An Address Map describes how the virtual devices are laid out on the bus. Each
# device carries its *logical* range (base / size / end) and the actual *bus
# attach ranges*. When a small device sits inside a larger one as a
# memory-mapped I/O window (e.g. UART inside RAM), the larger device records the
# carved-out window in ``reserved`` and the smaller one is tagged ``role="mmio"``
# / ``overlay=<kind>``. Only the bus attach ranges are checked for *unintended*
# overlap, so an intentional MMIO overlay is not flagged.


_MEMORY_KINDS = ("ram", "vram", "rom")


def build_address_map_from_devices(mode, device_specs) -> dict:
    """Build an Address Map from a list of *addressable* device specs.

    Each spec needs ``kind`` / ``base`` / ``size`` (+ optional ``node_id`` /
    ``device_id`` or ``runtime_id`` / ``label``). Memory-kind devices (ram/vram/rom)
    act as containers; a non-memory device that falls strictly inside a memory
    device becomes a carved-out MMIO overlay window (the memory device is attached
    around it). This generalises the RAM + UART carving of the legacy
    ``build_address_map()`` (PATCH_DEVICE_REGISTRY_REFACTOR_V08); for the 1-memory +
    1-window case the output is identical.
    """
    specs = [s for s in (device_specs or []) if s.get("addressable", True)]
    mem = [s for s in specs if s.get("kind") in _MEMORY_KINDS]

    def _dev_id(s):
        return s.get("device_id") or s.get("runtime_id") or s.get("kind")

    def _common(s, end):
        return {
            "kind": s.get("kind"), "node_id": s.get("node_id"),
            "device_id": _dev_id(s), "base": s["base"], "size": s["size"],
            "end": end, "label": s.get("label") or str(s.get("kind", "")).upper(),
            "readable": True, "writable": True,
        }

    devices = []
    for s in specs:
        end = s["base"] + s["size"] - 1
        if s.get("kind") in _MEMORY_KINDS:
            windows = []
            for w in specs:
                if w is s or w.get("kind") in _MEMORY_KINDS:
                    continue
                w_end = w["base"] + w["size"] - 1
                inside = (s["base"] <= w["base"]) and (w_end <= end)
                if inside and (w["base"] > s["base"] or w_end < end):
                    windows.append((w["base"], w_end))
            windows.sort()
            ranges, cursor = [], s["base"]
            for wb, we in windows:
                if wb > cursor:
                    ranges.append((cursor, wb - 1))
                cursor = we + 1
            if cursor <= end:
                ranges.append((cursor, end))
            if not windows:
                ranges = [(s["base"], end)]
            dev = _common(s, end)
            dev["role"] = "memory"
            dev["attach_ranges"] = ranges
            dev["reserved"] = windows
            devices.append(dev)
        else:
            inside_kind = None
            for m in mem:
                m_end = m["base"] + m["size"] - 1
                if (m["base"] <= s["base"]) and (end <= m_end):
                    inside_kind = m.get("kind")
                    break
            dev = _common(s, end)
            dev["role"] = "mmio" if inside_kind else "io"
            dev["attach_ranges"] = [(s["base"], end)]
            dev["overlay"] = inside_kind if inside_kind else None
            devices.append(dev)
    return {"mode": mode, "devices": devices}


def build_address_map(*, mode, ram_node, ram_base, ram_size,
                      uart_node, uart_base, uart_size,
                      ram_device_id="sim_ram", uart_device_id="sim_uart"):
    """Build an Address Map for a RAM + UART circuit (backward-compatible wrapper).

    Delegates to :func:`build_address_map_from_devices` (the device-list-driven
    builder). The output is identical to the previous RAM/UART-specific
    implementation: if the UART range falls strictly inside the RAM logical range,
    the RAM is attached around the UART window and the UART is an MMIO overlay.
    """
    specs = [
        {"kind": "ram", "node_id": ram_node, "device_id": ram_device_id,
         "base": ram_base, "size": ram_size, "label": "RAM", "addressable": True},
        {"kind": "uart", "node_id": uart_node, "device_id": uart_device_id,
         "base": uart_base, "size": uart_size, "label": "UART", "addressable": True},
    ]
    return build_address_map_from_devices(mode, specs)


def _ranges_overlap(a, b) -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def validate_address_map(amap: dict) -> list:
    """Return a list of *unintended* overlap issues (empty == valid).

    Only the actual bus ``attach_ranges`` are checked. A device's logical range
    may intentionally contain another device as an MMIO overlay window (e.g. UART
    inside RAM); that is represented separately and is NOT flagged here.
    """
    entries: list[tuple] = []   # (device_id, (lo, hi))
    for dev in amap.get("devices", []):
        for r in dev.get("attach_ranges", []):
            entries.append((dev.get("device_id", "?"), (r[0], r[1])))

    issues: list[str] = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            id_a, ra = entries[i]
            id_b, rb = entries[j]
            if _ranges_overlap(ra, rb):
                issues.append(
                    f"address overlap: {id_a} [{ra[0]:#06x}-{ra[1]:#06x}] "
                    f"vs {id_b} [{rb[0]:#06x}-{rb[1]:#06x}]"
                )
    return issues


def format_address_map_summary(amap: dict) -> list:
    """Return human-readable Address Map summary lines for the Log."""
    lines = ["Address Map:"]
    for dev in amap.get("devices", []):
        size = dev.get("size", 0)
        if size and size % 1024 == 0:
            size_str = f"{size // 1024}KB"
        else:
            size_str = f"{size}B"
        tag   = " MMIO" if dev.get("role") == "mmio" else ""
        label = dev.get("label", dev.get("kind", "?"))
        node  = dev.get("node_id") or "-"
        lines.append(
            f"  {label:<4} {node}  "
            f"{dev.get('base', 0):#06x}-{dev.get('end', 0):#06x}  {size_str}{tag}"
        )
    return lines
