# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Port connection validation (PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08).

Pure, Qt-independent checks over the v2 port schema (see ``core/ports.py``):
direction, bus role, signal width and base-kind compatibility.  Every problem is
returned as a structured *warning* issue dict — this module **never blocks, deletes
or mutates a connection**.  It is the single source of truth shared by the Canvas
(on connect), Port Detail, and any future Diagnostics panel.

Issue dict shape::

    {
        "severity": "warning" | "info",
        "code":     "PORT_WIDTH_MISMATCH",     # stable identifier
        "message":  "Port width mismatch: ...",
        "details":  {...},                      # code-specific extras
        # added by validate_connection / validate_node_connections:
        "from_node", "from_port", "to_node", "to_port", "conn_id",
    }
"""
from __future__ import annotations

from core.ports import base_port_type, normalize_port

SEVERITY_WARNING = "warning"
SEVERITY_INFO    = "info"

# Issue codes.
PORT_MULTIPLE_DRIVERS = "PORT_MULTIPLE_DRIVERS"   # out <-> out
PORT_NO_DRIVER        = "PORT_NO_DRIVER"          # in  <-> in
PORT_ROLE_MISMATCH    = "PORT_ROLE_MISMATCH"      # master<->master / slave<->slave
PORT_WIDTH_MISMATCH   = "PORT_WIDTH_MISMATCH"
PORT_KIND_MISMATCH    = "PORT_KIND_MISMATCH"
PORT_NOT_FOUND        = "PORT_NOT_FOUND"
SELF_CONNECTION       = "SELF_CONNECTION"
DUPLICATE_CONNECTION  = "DUPLICATE_CONNECTION"


def _issue(code: str, message: str, *, severity: str = SEVERITY_WARNING, **details) -> dict:
    return {"severity": severity, "code": code, "message": message, "details": dict(details)}


def _augment(issue: dict, from_node_id, from_port, to_node_id, to_port, conn_id) -> dict:
    out = dict(issue)
    out["from_node"] = from_node_id
    out["from_port"] = from_port
    out["to_node"]   = to_node_id
    out["to_port"]   = to_port
    out["conn_id"]   = conn_id
    return out


def find_port(part: "dict | None", port_name: str) -> "dict | None":
    """Return the port dict named *port_name* on *part*, or None."""
    if not isinstance(part, dict):
        return None
    for p in part.get("ports", []) or []:
        if p.get("name") == port_name:
            return p
    return None


def validate_port_pair(port_a: "dict | None", port_b: "dict | None") -> list:
    """Return warning issues for a pair of (v2) port dicts. Pure & symmetric.

    Missing / None attributes are skipped (never raises).  The issues carry
    severity / code / message / details only; endpoint node ids are added later
    by :func:`validate_connection`.
    """
    a = port_a or {}
    b = port_b or {}
    na = a.get("name", "?")
    nb = b.get("name", "?")
    issues: list = []

    # ---- direction ----
    da, db = a.get("direction"), b.get("direction")
    if da and db:
        if da == "out" and db == "out":
            issues.append(_issue(
                PORT_MULTIPLE_DRIVERS,
                f"Both ports drive (out↔out): {na} and {nb}",
                from_direction=da, to_direction=db))
        elif da == "in" and db == "in":
            issues.append(_issue(
                PORT_NO_DRIVER,
                f"Neither port drives (in↔in): {na} and {nb}",
                from_direction=da, to_direction=db))
        # out/in, inout/* combinations are OK

    # ---- role (bus master/slave) ----
    ra, rb = a.get("role"), b.get("role")
    if ra in ("master", "slave") and rb in ("master", "slave"):
        if ra == rb:
            issues.append(_issue(
                PORT_ROLE_MISMATCH,
                f"Bus role conflict: {na}={ra} and {nb}={rb}",
                from_role=ra, to_role=rb))
        # master<->slave is OK; role None on either side is skipped

    # ---- width ----
    wa, wb = a.get("width"), b.get("width")
    if wa is not None and wb is not None and wa != wb:
        issues.append(_issue(
            PORT_WIDTH_MISMATCH,
            f"Port width mismatch: {na} width={wa}, {nb} width={wb}",
            from_width=wa, to_width=wb))

    # ---- kind (base type) ----
    ka, kb = base_port_type(a.get("type")), base_port_type(b.get("type"))
    if ka and kb and ka != kb:
        issues.append(_issue(
            PORT_KIND_MISMATCH,
            f"Port kind mismatch: {na}={ka}, {nb}={kb}",
            from_kind=ka, to_kind=kb))

    return issues


def validate_connection(from_part: "dict | None", from_port_name: str,
                        to_part: "dict | None", to_port_name: str,
                        *,
                        from_node_id: "str | None" = None,
                        to_node_id: "str | None" = None,
                        conn_id: "str | None" = None) -> list:
    """Resolve ports by name (normalizing for derived v2 fields) and validate.

    If a port name is not found on its part, returns a single ``PORT_NOT_FOUND``
    warning and skips the pair checks. Never raises.
    """
    pa = find_port(from_part, from_port_name)
    pb = find_port(to_part, to_port_name)
    if pa is None or pb is None:
        missing = []
        if pa is None:
            missing.append(from_port_name)
        if pb is None:
            missing.append(to_port_name)
        return [_augment(
            _issue(PORT_NOT_FOUND,
                   f"Port not found: {', '.join(str(m) for m in missing)}",
                   missing=missing),
            from_node_id, from_port_name, to_node_id, to_port_name, conn_id)]

    pa = normalize_port(pa, part_id=(from_part or {}).get("id"))
    pb = normalize_port(pb, part_id=(to_part or {}).get("id"))
    return [_augment(i, from_node_id, from_port_name, to_node_id, to_port_name, conn_id)
            for i in validate_port_pair(pa, pb)]


def validate_node_connections(nodes: list, connections: list) -> list:
    """Validate every connection across a topology and aggregate the issues.

    nodes:       ``[{"node_id", "part"}]``
    connections: ``[{"id", "from": {...}, "to": {...}}]``

    Adds self-connection and duplicate-connection diagnostics on top of the
    per-connection port checks. Pure / read-only; never raises. (Intended for a
    future Diagnostics panel; the Canvas uses :func:`validate_connection` per wire.)
    """
    parts: dict = {}
    for n in nodes or []:
        if isinstance(n, dict) and n.get("node_id") is not None:
            parts[n["node_id"]] = n.get("part")

    issues: list = []
    seen: dict = {}
    for c in connections or []:
        frm = c.get("from", {}) or {}
        to  = c.get("to", {}) or {}
        fn, tn = frm.get("node_id"), to.get("node_id")
        fp = frm.get("logical_port") or frm.get("port")
        tp = to.get("logical_port") or to.get("port")
        cid = c.get("id")

        if fn is not None and fn == tn:
            issues.append(_augment(
                _issue(SELF_CONNECTION, f"Connection links a node to itself: {fn}"),
                fn, fp, tn, tp, cid))

        key = frozenset(((fn, fp), (tn, tp)))
        if key in seen:
            issues.append(_augment(
                _issue(DUPLICATE_CONNECTION,
                       f"Duplicate connection between {fn}:{fp} and {tn}:{tp}",
                       severity=SEVERITY_INFO, first=seen[key]),
                fn, fp, tn, tp, cid))
        else:
            seen[key] = cid

        issues.extend(validate_connection(
            parts.get(fn), fp, parts.get(tn), tp,
            from_node_id=fn, to_node_id=tn, conn_id=cid))
    return issues
