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


def resolve_circuit(nodes: list[dict], connections: list[dict]) -> dict:
    """Resolve a CircuitPlan from canvas *nodes* and *connections*.

    nodes:       [{"node_id", "category", "part_id", "name"}]
    connections: [{"from_node", "to_node"}]  (treated as undirected adjacency)

    Returns a dict::

        {
          "ok": bool,                 # True only when the circuit can execute
          "issues": [str],            # human-readable problems (empty when ok)
          "cpu": node_id | None,      # the CPU that will run
          "rams": [node_id],          # RAM parts wired to the CPU
          "uarts": [node_id],         # UART parts wired to the CPU
          "cpu_present": bool,        # any CPU placed at all (circuit-mode flag)
        }
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

    issues: list[str] = []
    cpu_present = len(cpus) > 0

    if len(cpus) == 0:
        issues.append("no CPU part on canvas")
        return {
            "ok": False, "issues": issues, "cpu": None,
            "rams": [], "uarts": [], "cpu_present": False,
        }
    if len(cpus) > 1:
        issues.append(f"multiple CPU parts ({len(cpus)}) — ambiguous, place exactly one")

    cpu = cpus[0]["node_id"]
    conn_rams  = [r["node_id"] for r in rams  if wired(cpu, r["node_id"])]
    conn_uarts = [u["node_id"] for u in uarts if wired(cpu, u["node_id"])]

    if not rams:
        issues.append("no RAM part on canvas")
    elif not conn_rams:
        issues.append(f"CPU {cpu} is not wired to any RAM")

    if not uarts:
        issues.append("no UART part on canvas")
    elif not conn_uarts:
        issues.append(f"CPU {cpu} is not wired to any UART")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "cpu": cpu,
        "rams": conn_rams,
        "uarts": conn_uarts,
        "cpu_present": cpu_present,
    }
