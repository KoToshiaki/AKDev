# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Port Detail panel — read-only view of a selected node/wire's ports + connections.

PATCH_PORT_DETAIL_V07: AKDev can place parts, grow Dynamic Visual Ports and wire
them, but there is no single place to inspect, for the selected part, its
part.json logical ports, its visual ports and every connection it takes part in.
This panel gathers that (via the Canvas' public read-only API) and renders it.

It owns no state and edits nothing — Properties stays the editor, Run Status stays
the execution summary, and this is the wiring/port debug view.  The ``build_*``
helpers are pure (canvas in, dict out) so they can be unit-tested, and
``render_detail`` is defensive (missing keys / None are fine).
"""
from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QPlainTextEdit, QWidget
from PySide6.QtCore import Qt


def direction_from_type(port_type: str) -> str:
    """Infer a port direction from its part.json ``type`` (no explicit field yet)."""
    t = (port_type or "").lower()
    if "master" in t:
        return "master (out)"
    if "slave" in t:
        return "slave (in)"
    if t in ("clock", "reset", "irq"):
        return "in"
    if "serial" in t:
        return "bidir"
    return "-"


# ---------------------------------------------------------------------------
# info builders (pure: take the Canvas' public API, return a plain dict)
# ---------------------------------------------------------------------------

def build_node_info(canvas, node_id: str) -> dict:
    """Build a Port Detail info dict for a selected node."""
    node = canvas.get_node(node_id)
    if node is None:
        return {"selection": "none"}
    part = node.part()
    pos  = node.pos()
    conns = canvas.node_connections(node_id)

    # visual port ids on this node that some connection references
    connected_vp: set = set()
    for c in conns:
        for end in (c.get("from", {}), c.get("to", {})):
            if end.get("node_id") == node_id and end.get("visual_port_id"):
                connected_vp.add(end["visual_port_id"])

    logical = []
    for p in part.get("ports", []) or []:
        t = p.get("type", "")
        # PATCH_PORT_SCHEMA_V08: prefer explicit v2 fields; fall back to type-based
        # inference for legacy (v1) ports that lack them.
        direction = p.get("direction") or direction_from_type(t)
        width = p.get("width")
        logical.append({
            "name":      p.get("name", "?"),
            "type":      t or "-",
            "role":      p.get("role"),
            "direction": direction,
            "width":     width if width is not None else "-",
            "description": p.get("description", ""),
        })

    visual = []
    for vp in node.visual_ports():
        vp_id = vp.get("id")
        visual.append({
            "id":        vp_id,
            "label":     vp.get("label", "-"),
            "side":      vp.get("side", "-"),
            "offset":    vp.get("offset", "-"),
            "kind":      vp.get("kind", "-"),
            "locked":    bool(vp.get("locked", False)),
            "connected": vp_id in connected_vp,
        })

    connections = []
    for c in conns:
        frm, to = c.get("from", {}), c.get("to", {})
        if frm.get("node_id") == node_id:
            peer, direction = to, "out"
        else:
            peer, direction = frm, "in"
        peer_node = peer.get("node_id")
        peer_part_node = canvas.get_node(peer_node) if peer_node else None
        peer_part = peer_part_node.part().get("name") if peer_part_node else "?"
        connections.append({
            "id":        c.get("id"),
            "from_node": frm.get("node_id"),
            "to_node":   to.get("node_id"),
            "from_port": frm.get("logical_port") or frm.get("port"),
            "to_port":   to.get("logical_port") or to.get("port"),
            "peer_node": peer_node,
            "peer_part": peer_part,
            "direction": direction,
            "kind":      c.get("kind"),
            "width":     c.get("width"),
            "style":     c.get("style"),
        })

    return {
        "selection":     "node",
        "node_id":       node_id,
        "part_id":       part.get("id"),
        "part_name":     part.get("name"),
        "category":      part.get("category"),
        "pos":           (round(pos.x(), 2), round(pos.y(), 2)),
        "logical_ports": logical,
        "visual_ports":  visual,
        "connections":   connections,
        # PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08: issues of all connections here.
        "validation":    canvas.node_validation_issues(node_id),
    }


def build_wire_info(canvas, conn_id: str) -> dict:
    """Build a Port Detail info dict for a selected wire/connection."""
    c = canvas.get_connection(conn_id)
    if c is None:
        return {"selection": "none"}
    frm, to = c.get("from", {}), c.get("to", {})
    from_node, to_node = frm.get("node_id"), to.get("node_id")
    fn = canvas.get_node(from_node) if from_node else None
    tn = canvas.get_node(to_node) if to_node else None
    return {
        "selection": "wire",
        "id":        c.get("id"),
        "kind":      c.get("kind"),
        "width":     c.get("width"),
        "from_node": from_node,
        "to_node":   to_node,
        "from_port": frm.get("logical_port") or frm.get("port"),
        "to_port":   to.get("logical_port") or to.get("port"),
        "from_part": fn.part().get("name") if fn else "?",
        "to_part":   tn.part().get("name") if tn else "?",
        "from_vp":   frm.get("visual_port_id"),
        "to_vp":     to.get("visual_port_id"),
        "style":     c.get("style"),
        # PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08: this connection's issues.
        "validation": canvas.connection_validation(conn_id),
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def _render_validation(issues: "list | None") -> list:
    """Render a Validation section (PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08)."""
    lines = ["Validation"]
    issues = issues or []
    if not issues:
        lines.append("  OK")
        return lines
    for i in issues:
        sev    = str(i.get("severity", "warning")).upper()
        conn   = f" ({i['conn_id']})" if i.get("conn_id") else ""
        lines.append(f"  {sev} {i.get('code')}: {i.get('message')}{conn}")
    return lines


def _render_node(info: dict) -> list[str]:
    lines = ["=== Port Detail ===", "Selection: node"]
    lines.append(f"Node: {info.get('node_id')}")
    lines.append(f"Part: {info.get('part_name')} ({info.get('part_id')})")
    lines.append(f"Category: {info.get('category')}")
    pos = info.get("pos")
    if pos:
        lines.append(f"Position: ({pos[0]}, {pos[1]})")
    lines.append("")

    lines.append("Logical Ports")
    lp = info.get("logical_ports") or []
    if lp:
        for p in lp:
            role = f" role={p.get('role')}" if p.get("role") else ""
            desc = f"  — {p.get('description')}" if p.get("description") else ""
            lines.append(
                f"  {p.get('name')}: kind={p.get('type')}{role} "
                f"dir={p.get('direction')} width={p.get('width')}{desc}"
            )
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("Visual Ports")
    vp = info.get("visual_ports") or []
    if vp:
        for v in vp:
            state = "connected" if v.get("connected") else "unconnected"
            lock = " locked" if v.get("locked") else ""
            lines.append(
                f"  {v.get('id')} [{v.get('label')}] side={v.get('side')} "
                f"offset={v.get('offset')} kind={v.get('kind')} {state}{lock}"
            )
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append("Connections")
    conns = info.get("connections") or []
    if conns:
        for c in conns:
            extra = " style" if c.get("style") else ""
            lines.append(
                f"  {c.get('id')} {c.get('direction')} -> {c.get('peer_node')} "
                f"({c.get('peer_part')})"
            )
            lines.append(
                f"    {c.get('from_node')}:{c.get('from_port')} -> "
                f"{c.get('to_node')}:{c.get('to_port')} "
                f"kind={c.get('kind')} width={c.get('width')}{extra}"
            )
    else:
        lines.append("  (none)")
    lines.append("")
    lines += _render_validation(info.get("validation"))
    return lines


def _render_wire(info: dict) -> list[str]:
    lines = ["=== Port Detail ===", "Selection: wire"]
    lines.append(f"Connection: {info.get('id')}")
    lines.append(f"Kind: {info.get('kind')}   Width: {info.get('width')}")
    lines.append(
        f"From: {info.get('from_node')}:{info.get('from_port')} "
        f"({info.get('from_part')})  vp={info.get('from_vp')}"
    )
    lines.append(
        f"To:   {info.get('to_node')}:{info.get('to_port')} "
        f"({info.get('to_part')})  vp={info.get('to_vp')}"
    )
    style = info.get("style")
    if style:
        lines.append(f"Style: {style}")
    else:
        lines.append("Style: (default)")
    lines.append("")
    lines += _render_validation(info.get("validation"))
    return lines


def render_detail(info: dict) -> str:
    """Render a Port Detail info dict into a human-readable multi-line string."""
    info = info or {}
    sel = info.get("selection", "none")
    if sel == "node":
        return "\n".join(_render_node(info))
    if sel == "wire":
        return "\n".join(_render_wire(info))
    return "=== Port Detail ===\nNo node or wire selected"


class PortDetailPanel(QDockWidget):
    """Dock panel showing the selected node/wire's ports and connections."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Port Detail", parent)
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
            | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setPlaceholderText("Select a node or wire...")
        font = self._text.font()
        font.setFamily("Courier New")
        font.setPointSize(9)
        self._text.setFont(font)
        self.setWidget(self._text)
        self._info: dict = {}

    # ------------------------------------------------------------------ public

    def update_detail(self, info: dict) -> None:
        """Refresh the panel from a Port Detail info snapshot."""
        self._info = dict(info or {})
        self._text.setPlainText(render_detail(self._info))

    def detail_text(self) -> str:
        """Return the current rendered detail text (for tests / inspection)."""
        return self._text.toPlainText()
