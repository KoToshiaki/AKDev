# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Bus protocol validation (PATCH_BUS_PROTOCOL_VALIDATION_V08).

Pure, Qt-independent checks one level above ``core/port_validation.py``: instead of
a single port pair, it looks at the whole *bus structure*.  Bus ports joined by bus
connections form **bus groups** (port-level connected components), and each group is
checked for a sane master/slave count:

  * no master      -> BUS_NO_MASTER
  * 2+ masters     -> BUS_MULTIPLE_MASTERS
  * no slave       -> BUS_NO_SLAVE

Every problem is a structured *warning* issue (shape-compatible with
``core/port_validation.py``).  This module **never blocks, deletes or mutates a
connection**, and it never changes the circuit / target-CPU resolution.

Out of scope (deferred): bus-bridge routing, multi-hop reachability, Address Map
cross-checking.  ``target_cpu_id`` / ``address_map`` are accepted for forward
compatibility but only annotate group membership for now.
"""
from __future__ import annotations

from core.ports import base_port_type, normalize_port

SEVERITY_WARNING = "warning"
SEVERITY_INFO    = "info"

# Issue codes.
BUS_NO_MASTER        = "BUS_NO_MASTER"
BUS_MULTIPLE_MASTERS = "BUS_MULTIPLE_MASTERS"
BUS_NO_SLAVE         = "BUS_NO_SLAVE"


def is_bus_port(port: "dict | None") -> bool:
    """True if *port* is a bus-kind port (``base_port_type(type) == 'bus'``)."""
    return bool(port) and base_port_type(port.get("type")) == "bus"


def _find_port(part: "dict | None", port_name) -> "dict | None":
    if not isinstance(part, dict):
        return None
    for p in part.get("ports", []) or []:
        if p.get("name") == port_name:
            return p
    return None


def _endpoint_port_name(end: dict):
    return end.get("logical_port") or end.get("port")


def build_bus_groups(nodes: list, connections: list) -> list:
    """Group bus ports into connected components over bus edges (port-level).

    nodes:       ``[{"node_id", "part"}]``
    connections: ``[{"id", "from": {...}, "to": {...}}]``

    A *bus edge* is a connection whose **both** endpoint ports are bus ports; all
    other connections are ignored.  Endpoints are ``(node_id, port_name)`` so a part
    with two bus ports (e.g. a bridge's master + slave) can land in two groups.
    Only ports reached by at least one bus edge appear (lone, unconnected bus ports
    are not grouped). Pure / never raises.
    """
    parts: dict = {}
    for n in nodes or []:
        if isinstance(n, dict) and n.get("node_id") is not None:
            parts[n["node_id"]] = n.get("part")

    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:        # path compression
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    meta: dict = {}          # endpoint -> {node_id, part_id, port, role}
    edges: list = []         # (ep_a, ep_b, conn_id)

    for c in connections or []:
        frm = c.get("from", {}) or {}
        to  = c.get("to", {}) or {}
        fn, tn = frm.get("node_id"), to.get("node_id")
        fp, tp = _endpoint_port_name(frm), _endpoint_port_name(to)
        fport = _find_port(parts.get(fn), fp)
        tport = _find_port(parts.get(tn), tp)
        if not (is_bus_port(fport) and is_bus_port(tport)):
            continue   # not a bus edge — ignored
        ep_a, ep_b = (fn, fp), (tn, tp)
        npa = normalize_port(fport, part_id=(parts.get(fn) or {}).get("id"))
        npb = normalize_port(tport, part_id=(parts.get(tn) or {}).get("id"))
        meta[ep_a] = {"node_id": fn, "part_id": (parts.get(fn) or {}).get("id"),
                      "port": fp, "role": npa.get("role")}
        meta[ep_b] = {"node_id": tn, "part_id": (parts.get(tn) or {}).get("id"),
                      "port": tp, "role": npb.get("role")}
        union(ep_a, ep_b)
        edges.append((ep_a, ep_b, c.get("id")))

    members: dict = {}       # root -> [endpoint]
    for ep in meta:
        members.setdefault(find(ep), []).append(ep)

    conns_by_root: dict = {}
    for ep_a, _ep_b, cid in edges:
        r = find(ep_a)
        bucket = conns_by_root.setdefault(r, [])
        if cid is not None and cid not in bucket:
            bucket.append(cid)

    # Deterministic group order/ids (stable for a given canvas state).
    roots = sorted(members, key=lambda r: sorted(str(e) for e in members[r])[0])
    groups: list = []
    for i, root in enumerate(roots, 1):
        ports = sorted((meta[ep] for ep in members[root]),
                       key=lambda p: (str(p["node_id"]), str(p["port"])))
        node_ids: list = []
        for p in ports:
            if p["node_id"] not in node_ids:
                node_ids.append(p["node_id"])
        groups.append({
            "id":          f"bus_group_{i:04d}",
            "nodes":       node_ids,
            "ports":       ports,
            "masters":     [p for p in ports if p["role"] == "master"],
            "slaves":      [p for p in ports if p["role"] == "slave"],
            "connections": sorted(conns_by_root.get(root, [])),
        })
    return groups


def validate_bus_group(group: dict) -> list:
    """Return warning issues for a single bus group's master/slave counts."""
    gid     = group.get("id")
    nodes   = list(group.get("nodes", []))
    conns   = list(group.get("connections", []))
    masters = group.get("masters", [])
    slaves  = group.get("slaves", [])

    def _mk(code, message, **details):
        return {"severity": SEVERITY_WARNING, "code": code, "message": message,
                "group_id": gid, "nodes": nodes, "connections": conns,
                "details": details}

    def _label(ports):
        return [f"{p['node_id']}:{p['port']}" for p in ports]

    issues: list = []
    if len(masters) == 0:
        issues.append(_mk(BUS_NO_MASTER,
            f"Bus group {gid} has no master", slaves=_label(slaves)))
    elif len(masters) >= 2:
        issues.append(_mk(BUS_MULTIPLE_MASTERS,
            f"Bus group {gid} has multiple masters: "
            + ", ".join(str(p["part_id"]) for p in masters),
            masters=_label(masters)))
    if len(slaves) == 0:
        issues.append(_mk(BUS_NO_SLAVE,
            f"Bus group {gid} has no slave", masters=_label(masters)))
    return issues


def validate_bus_protocol(nodes: list, connections: list, *,
                          target_cpu_id: "str | None" = None,
                          address_map: "dict | None" = None) -> list:
    """Build bus groups and validate each. Returns aggregated warning issues.

    ``target_cpu_id`` (if given) annotates each issue's ``details`` with whether the
    target CPU is in that group. ``address_map`` is accepted for forward
    compatibility (cross-checking is deferred to a later patch).
    """
    issues: list = []
    for group in build_bus_groups(nodes, connections):
        group_issues = validate_bus_group(group)
        if target_cpu_id is not None:
            in_group = any(p.get("node_id") == target_cpu_id for p in group["ports"])
            for issue in group_issues:
                issue["details"]["target_cpu_in_group"] = in_group
        issues.extend(group_issues)
    return issues
