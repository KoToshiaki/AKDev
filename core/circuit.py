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


def _is_cpu(node: dict) -> bool:
    return node.get("category") == "cpu"


def _is_ram(node: dict) -> bool:
    return node.get("category") == "mem"


def _is_uart(node: dict) -> bool:
    if node.get("category") != "io":
        return False
    tag = (str(node.get("part_id", "")) + " " + str(node.get("name", ""))).lower()
    return "uart" in tag


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
    # must not block the target's execution.
    conn_rams  = [r["node_id"] for r in rams  if wired(target, r["node_id"])]
    conn_uarts = [u["node_id"] for u in uarts if wired(target, u["node_id"])]

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


def build_address_map(*, mode, ram_node, ram_base, ram_size,
                      uart_node, uart_base, uart_size,
                      ram_device_id="sim_ram", uart_device_id="sim_uart"):
    """Build an Address Map for a RAM + UART circuit.

    Returns ``{"mode": mode, "devices": [ram_dev, uart_dev]}``. If the UART range
    falls strictly inside the RAM logical range, the RAM is attached around the
    UART window (so the bus has no real overlap) and the UART is marked as an MMIO
    overlay. Otherwise RAM and UART get a single attach range each.
    """
    ram_end  = ram_base + ram_size - 1
    uart_end = uart_base + uart_size - 1

    uart_inside = (ram_base <= uart_base) and (uart_end <= ram_end)
    carves = uart_inside and (uart_base > ram_base or uart_end < ram_end)
    if carves:
        ram_ranges = []
        if uart_base > ram_base:
            ram_ranges.append((ram_base, uart_base - 1))
        if uart_end < ram_end:
            ram_ranges.append((uart_end + 1, ram_end))
        reserved = [(uart_base, uart_end)]
    else:
        ram_ranges = [(ram_base, ram_end)]
        reserved = []

    ram_dev = {
        "kind": "ram", "node_id": ram_node, "device_id": ram_device_id,
        "base": ram_base, "size": ram_size, "end": ram_end, "label": "RAM",
        "role": "memory", "readable": True, "writable": True,
        "attach_ranges": ram_ranges, "reserved": reserved,
    }
    uart_dev = {
        "kind": "uart", "node_id": uart_node, "device_id": uart_device_id,
        "base": uart_base, "size": uart_size, "end": uart_end, "label": "UART",
        "role": "mmio" if uart_inside else "io", "readable": True, "writable": True,
        "attach_ranges": [(uart_base, uart_end)],
        "overlay": "ram" if uart_inside else None,
    }
    return {"mode": mode, "devices": [ram_dev, uart_dev]}


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
