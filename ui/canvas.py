# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""System Canvas — QGraphicsView with draggable PartNode items."""
from collections import deque
from math import floor, ceil
from PySide6.QtCore import Qt, QPoint, QRectF, QPointF, Signal
from PySide6.QtGui import QColor, QBrush, QPen, QFont, QPainterPath
from PySide6.QtWidgets import (QGraphicsEllipseItem, QGraphicsItem,
                                QGraphicsPathItem, QGraphicsRectItem,
                                QGraphicsScene, QGraphicsView, QMenu)


_NODE_W = 140
_NODE_H = 56

_CAT_COLOR = {
    "fpga":   QColor("#5b9bd5"),
    "cpu":    QColor("#70ad47"),
    "mem":    QColor("#ffc000"),
    "io":     QColor("#ed7d31"),
    "video":  QColor("#9b59b6"),
    "bus":    QColor("#95a5a6"),
    "debug":  QColor("#e74c3c"),
    "custom": QColor("#bdc3c7"),
}
_DEFAULT_COLOR = QColor("#cccccc")

_ZOOM_MIN      = 0.1
_ZOOM_MAX      = 10.0
_PAN_THRESHOLD = 4    # Manhattan px before right-drag activates pan

_KIND_COLORS = {
    "bus":    "#66ccff",
    "signal": "#88ddaa",
    "clock":  "#ffcc66",
    "reset":  "#ff8888",
}
_KIND_PEN_WIDTH     = {"bus": 3.0, "signal": 1.5, "clock": 1.5, "reset": 1.5}
_WIRE_PREVIEW_COLOR = QColor("#ffaa00")

_DOT_RADIUS  = 5
_DOT_COLOR   = QColor("#4a90d9")   # blue
_DOT_PENDING = QColor("#f5a623")   # amber when selected as pending


class GridScene(QGraphicsScene):
    """QGraphicsScene with an optional grid drawn in drawBackground()."""

    GRID_SIZE = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid_visible = True

    def set_grid_visible(self, enabled: bool) -> None:
        self._grid_visible = enabled
        self.update()

    def grid_visible(self) -> bool:
        return self._grid_visible

    def drawBackground(self, painter, rect) -> None:
        super().drawBackground(painter, rect)
        if not self._grid_visible:
            return
        g    = float(self.GRID_SIZE)
        left = (rect.left() // g) * g
        top  = (rect.top()  // g) * g
        painter.setPen(QPen(QColor(220, 220, 220), 0.5))
        x = left
        while x <= rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += g
        y = top
        while y <= rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += g


def _grid_pos(p: QPointF) -> tuple:
    """Convert scene point to integer grid cell (col, row)."""
    g = GridScene.GRID_SIZE
    return (round(p.x() / g), round(p.y() / g))


def _compress_path(path: list) -> list:
    """Remove interior cells where direction is unchanged (keep turning points)."""
    if len(path) <= 2:
        return list(path)
    result = [path[0]]
    for i in range(1, len(path) - 1):
        d1 = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        d2 = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        if d1 != d2:
            result.append(path[i])
    result.append(path[-1])
    return result


class ConnectionLine(QGraphicsPathItem):
    """Visual line connecting two PartNodes; sits behind nodes (zValue -1)."""

    def __init__(self, conn_id: str, from_node_id: str, to_node_id: str,
                 kind: str = "bus", color: str = ""):
        super().__init__()
        self._conn_id      = conn_id
        self._from_node_id = from_node_id
        self._to_node_id   = to_node_id
        self._kind         = kind
        c = QColor(color) if color else QColor(_KIND_COLORS.get(kind, "#aaaaaa"))
        self._base_pen = QPen(c, _KIND_PEN_WIDTH.get(kind, 1.5))
        self.setPen(self._base_pen)
        self.setZValue(-1)

    def conn_id(self) -> str:
        return self._conn_id

    def from_node_id(self) -> str:
        return self._from_node_id

    def to_node_id(self) -> str:
        return self._to_node_id

    def kind(self) -> str:
        return self._kind

    def set_active(self, active: bool) -> None:
        """Highlight the line when active (bus transaction occurred)."""
        if active:
            bright = self._base_pen.color().lighter(160)
            self.setPen(QPen(bright, self._base_pen.widthF() + 1.5))
        else:
            self.setPen(self._base_pen)

    def update_route(self, points: list) -> None:
        """Draw straight segments through the given corner points.

        Points are expected to already be H/V-aligned (e.g. from BFS compression),
        so a simple lineTo chain produces clean right-angle routing.
        """
        if len(points) < 2:
            return
        path = QPainterPath(points[0])
        for p in points[1:]:
            path.lineTo(p)
        self.setPath(path)

    def update_line(self, p1: QPointF, p2: QPointF) -> None:
        """Draw an H-then-V right-angle path from p1 to p2."""
        mid = QPointF(p2.x(), p1.y())
        self.update_route([p1, mid, p2])


class PortDot(QGraphicsEllipseItem):
    """Port indicator on a PartNode; visual only — wire mode via right-click menu."""

    def __init__(self, node_id: str, port_name: str, parent: "QGraphicsItem"):
        r = _DOT_RADIUS
        super().__init__(-r, -r, r * 2, r * 2, parent)
        self._node_id   = node_id
        self._port_name = port_name
        self._click_cb  = None   # kept for legacy direct-API tests (_on_port_click)
        self.setPen(QPen(QColor("#333333"), 1))
        self.setBrush(QBrush(_DOT_COLOR))
        self.setZValue(1)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def node_id(self) -> str:
        return self._node_id

    def port_name(self) -> str:
        return self._port_name

    def set_pending(self, pending: bool) -> None:
        self.setBrush(QBrush(_DOT_PENDING if pending else _DOT_COLOR))

    def mousePressEvent(self, event) -> None:
        if self._click_cb is not None:
            self._click_cb(self)
        event.accept()


class RouteHandle(QGraphicsRectItem):
    """Draggable waypoint handle displayed on route paths in wire mode."""

    _S = 6

    def __init__(self, conn_id: str, pt_idx: int, pos: QPointF,
                 moved_cb: "callable"):
        r = self._S / 2
        super().__init__(-r, -r, self._S, self._S)
        self._conn_id  = conn_id
        self._pt_idx   = pt_idx
        self._moved_cb = moved_cb
        self.setPen(QPen(QColor("#ffffff"), 1))
        self.setBrush(QBrush(QColor("#ffaa00")))
        self.setZValue(2)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPos(pos)

    def conn_id(self) -> str:
        return self._conn_id

    def pt_idx(self) -> int:
        return self._pt_idx

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            g = float(GridScene.GRID_SIZE)
            return QPointF(round(value.x() / g) * g, round(value.y() / g) * g)
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._moved_cb(self._conn_id, self._pt_idx, value)
        return result


class PartNode(QGraphicsItem):
    """A single draggable/selectable part rectangle on the canvas."""

    def __init__(self, part: dict, node_id: str, sources: dict | None = None):
        super().__init__()
        self._part            = part
        self._node_id         = node_id
        self._snap_enabled    = False
        self._pos_changed_cb  = None   # called by Canvas after position changes
        self._sources: dict = (
            sources if sources is not None else {"asm": None, "hdl": None}
        )
        self._port_dot = PortDot(node_id, "bus", self)
        self._port_dot.setPos(_NODE_W, _NODE_H / 2)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def part(self) -> dict:
        return self._part

    def node_id(self) -> str:
        return self._node_id

    def sources(self) -> dict:
        return self._sources

    def set_source(self, key: str, path: "str | None") -> None:
        self._sources[key] = path

    def set_snap(self, enabled: bool) -> None:
        self._snap_enabled = enabled

    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
                and self._snap_enabled):
            g     = float(GridScene.GRID_SIZE)
            value = QPointF(round(value.x() / g) * g, round(value.y() / g) * g)
        result = super().itemChange(change, value)
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
                and self._pos_changed_cb is not None):
            self._pos_changed_cb()
        return result

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, _NODE_W, _NODE_H)

    def paint(self, painter, option, widget=None):
        fill   = _CAT_COLOR.get(self._part.get("category", ""), _DEFAULT_COLOR)
        sel    = self.isSelected()
        border = QPen(QColor("#ffffff") if sel else QColor("#333333"), 2 if sel else 1)
        painter.setPen(border)
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(0, 0, _NODE_W, _NODE_H, 6, 6)

        painter.setPen(QColor("#111111"))
        f_bold = QFont("sans-serif", 9)
        f_bold.setBold(True)
        painter.setFont(f_bold)
        painter.drawText(
            QRectF(6, 4, _NODE_W - 12, _NODE_H // 2 - 2),
            Qt.AlignmentFlag.AlignVCenter,
            self._part.get("name", "?"),
        )
        painter.setFont(QFont("sans-serif", 7))
        painter.drawText(
            QRectF(6, _NODE_H // 2, _NODE_W - 12, _NODE_H // 2 - 4),
            Qt.AlignmentFlag.AlignVCenter,
            self._part.get("id", ""),
        )


class Canvas(QGraphicsView):
    """Main system canvas — hosts PartNode items."""

    selection_changed  = Signal(list)              # list[PartNode]
    tab_open_requested = Signal(dict, str, str)   # (part, node_id, ext)
    mode_changed       = Signal(str)              # "wire" | "design"

    def __init__(self, log_fn=None):
        super().__init__()
        self.setScene(GridScene(self))
        self._log            = log_fn or (lambda s: None)
        self._node_seq       = 0
        self._conn_seq:    int        = 0
        self._connections: list[dict] = []
        self._conn_items:   dict      = {}    # conn_id -> ConnectionLine
        self._pending_port            = None  # PortDot | None (legacy state machine)
        self._add_offset     = 0
        self._part_library: dict = {}
        self._snap_enabled: bool             = False
        self._pan_origin:   "QPoint | None" = None
        self._pan_last:     "QPoint | None" = None
        self._panned:       bool            = False
        self._mode:         str             = "design"
        self._wire_from:    "dict | None"   = None   # {"node_id", "port_name"}
        self._wire_waypoints: list          = []      # list[QPointF]
        self._wire_preview: "QGraphicsPathItem | None" = None
        self._handle_items: list            = []      # list[RouteHandle]
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setAcceptDrops(True)
        self.scene().selectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------ private

    def _on_selection_changed(self):
        items = [i for i in self.scene().selectedItems() if isinstance(i, PartNode)]
        self.selection_changed.emit(items)

    def _next_node_id(self) -> str:
        self._node_seq += 1
        return f"node_{self._node_seq:04d}"

    def _next_conn_id(self) -> str:
        self._conn_seq += 1
        return f"conn_{self._conn_seq:04d}"

    def _node_center(self, node_id: str) -> "QPointF | None":
        node = self.get_node(node_id)
        if node is None:
            return None
        return node.pos() + QPointF(_NODE_W / 2, _NODE_H / 2)

    def _from_port_pos(self, node_id: str) -> "QPointF | None":
        """Right-edge port position; wire exits from here."""
        node = self.get_node(node_id)
        return node.pos() + QPointF(_NODE_W, _NODE_H / 2) if node else None

    def _to_port_pos(self, node_id: str) -> "QPointF | None":
        """Left-edge port position; wire enters here."""
        node = self.get_node(node_id)
        return node.pos() + QPointF(0.0, _NODE_H / 2) if node else None

    def _make_conn_item(self, conn: dict) -> ConnectionLine:
        line = ConnectionLine(
            conn["id"],
            conn["from"]["node_id"],
            conn["to"]["node_id"],
            conn.get("kind", "bus"),
            conn.get("color", ""),
        )
        self.scene().addItem(line)
        return line

    def _on_port_click(self, dot: "PortDot") -> None:
        """Legacy 2-step state machine; available for direct API / test use."""
        if self._pending_port is None:
            self._pending_port = dot
            dot.set_pending(True)
        else:
            from_dot = self._pending_port
            from_dot.set_pending(False)
            self._pending_port = None
            if from_dot.node_id() == dot.node_id():
                return
            self.add_connection(
                from_dot.node_id(), from_dot.port_name(),
                dot.node_id(), dot.port_name(),
            )

    def _rebuild_conn_items(self) -> None:
        for item in self._conn_items.values():
            if item.scene() is not None:
                self.scene().removeItem(item)
        self._conn_items.clear()
        for conn in self._connections:
            self._conn_items[conn["id"]] = self._make_conn_item(conn)
        self.update_connections()

    def _block_cells(self, excl_ids: set) -> set:
        """Return grid cells occupied by PartNodes (with 1-cell margin), excluding excl_ids."""
        g = float(GridScene.GRID_SIZE)
        blocked: set = set()
        for item in self.scene().items():
            if not isinstance(item, PartNode):
                continue
            if item.node_id() in excl_ids:
                continue
            pos = item.pos()
            c0 = floor(pos.x() / g) - 1
            c1 = ceil((pos.x() + _NODE_W) / g) + 1
            r0 = floor(pos.y() / g) - 1
            r1 = ceil((pos.y() + _NODE_H) / g) + 1
            for c in range(c0, c1 + 1):
                for r in range(r0, r1 + 1):
                    blocked.add((c, r))
        return blocked

    def _route_segment(self, start: QPointF, end: QPointF, blocked: set) -> list:
        """BFS single-segment route from start to end avoiding blocked cells."""
        g = float(GridScene.GRID_SIZE)
        sc = _grid_pos(start)
        ec = _grid_pos(end)
        if sc == ec:
            return [start, end]
        margin = 10
        min_c = min(sc[0], ec[0]) - margin
        max_c = max(sc[0], ec[0]) + margin
        min_r = min(sc[1], ec[1]) - margin
        max_r = max(sc[1], ec[1]) + margin
        parent: dict = {sc: None}
        queue: deque = deque([sc])
        found = False
        while queue:
            c, r = queue.popleft()
            if (c, r) == ec:
                found = True
                break
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc, nr = c + dc, r + dr
                if (nc, nr) in parent:
                    continue
                if not (min_c <= nc <= max_c and min_r <= nr <= max_r):
                    continue
                if (nc, nr) in blocked:
                    continue
                parent[(nc, nr)] = (c, r)
                queue.append((nc, nr))
        if not found:
            return [start, QPointF(end.x(), start.y()), end]
        path: list = []
        cur = ec
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        compressed = _compress_path(path)
        return [QPointF(col * g, row * g) for col, row in compressed]

    def _route_grid(self, start: QPointF, end: QPointF,
                    waypoints: list, blocked: set) -> list:
        """Route all segments through waypoints using BFS; preserve exact endpoints."""
        checkpoints = [start] + waypoints + [end]
        all_pts: list = []
        for i in range(len(checkpoints) - 1):
            seg = self._route_segment(checkpoints[i], checkpoints[i + 1], blocked)
            if all_pts:
                all_pts.extend(seg[1:])
            else:
                all_pts.extend(seg)
        if all_pts:
            all_pts[0]  = start
            all_pts[-1] = end
        return all_pts

    def _show_handles(self) -> None:
        """Add RouteHandle items for every stored waypoint across all connections."""
        self._hide_handles()
        for conn in self._connections:
            for i, pt in enumerate(conn.get("route", [])):
                h = RouteHandle(conn["id"], i,
                                QPointF(pt["x"], pt["y"]),
                                self._on_handle_moved)
                self.scene().addItem(h)
                self._handle_items.append(h)

    def _hide_handles(self) -> None:
        """Remove all RouteHandle items from the scene."""
        for h in self._handle_items:
            if h.scene() is not None:
                self.scene().removeItem(h)
        self._handle_items = []

    def _on_handle_moved(self, conn_id: str, pt_idx: int,
                         new_pos: QPointF) -> None:
        """Update conn route data when a handle is dragged."""
        for conn in self._connections:
            if conn["id"] == conn_id:
                route = conn.get("route", [])
                if 0 <= pt_idx < len(route):
                    route[pt_idx] = {"x": new_pos.x(), "y": new_pos.y()}
                break
        self.update_connections()

    def _start_wire(self, node_id: str, port_name: str) -> None:
        """Enter wire mode starting from node_id:port_name."""
        self._mode = "wire"
        self._wire_from = {"node_id": node_id, "port_name": port_name}
        self._wire_waypoints = []
        preview = QGraphicsPathItem()
        preview.setPen(QPen(_WIRE_PREVIEW_COLOR, 1.5, Qt.PenStyle.DashLine))
        preview.setZValue(-0.5)
        self.scene().addItem(preview)
        self._wire_preview = preview
        self._show_handles()
        self.mode_changed.emit("wire")

    def _add_waypoint(self, scene_pos: QPointF) -> None:
        """Snap scene_pos to grid and append as a wire waypoint."""
        g = float(GridScene.GRID_SIZE)
        snapped = QPointF(round(scene_pos.x() / g) * g,
                          round(scene_pos.y() / g) * g)
        self._wire_waypoints.append(snapped)

    def _finish_wire(self, to_node_id: str, to_port_name: str) -> None:
        """Complete the in-progress wire and create a logical connection."""
        if self._wire_from is None:
            return
        from_info = self._wire_from
        waypoints = list(self._wire_waypoints)
        self._cancel_wire()
        self.add_connection(
            from_info["node_id"], from_info["port_name"],
            to_node_id, to_port_name,
            route=waypoints,
        )

    def _cancel_wire(self) -> None:
        """Abort wire mode and remove the preview item."""
        if self._wire_preview is not None and self._wire_preview.scene() is not None:
            self.scene().removeItem(self._wire_preview)
        self._wire_preview = None
        self._wire_from = None
        self._wire_waypoints = []
        self._hide_handles()
        self._mode = "design"
        self.mode_changed.emit("design")

    def _update_wire_preview(self, cursor_scene_pos: QPointF) -> None:
        """Redraw dashed preview from wire start through waypoints to cursor."""
        if self._wire_preview is None or self._wire_from is None:
            return
        start = self._from_port_pos(self._wire_from["node_id"])
        if start is None:
            return
        g = float(GridScene.GRID_SIZE)
        snapped = QPointF(round(cursor_scene_pos.x() / g) * g,
                          round(cursor_scene_pos.y() / g) * g)
        points = [start] + self._wire_waypoints + [snapped]
        path = QPainterPath(points[0])
        for i in range(1, len(points)):
            mid = QPointF(points[i].x(), points[i - 1].y())
            path.lineTo(mid)
            path.lineTo(points[i])
        self._wire_preview.setPath(path)

    # ------------------------------------------------------------------ public

    def set_mode(self, mode: str) -> None:
        """Switch canvas mode. 'design' cancels any active wire state."""
        if mode == self._mode:
            return
        if mode == "design":
            self._cancel_wire()  # sets _mode, hides handles, emits signal
        else:
            self._mode = "wire"
            self._show_handles()
            self.mode_changed.emit("wire")

    def update_connections(self) -> None:
        """Refresh all connection lines using port positions and obstacle-aware BFS routing."""
        g = float(GridScene.GRID_SIZE)
        for conn in self._connections:
            line = self._conn_items.get(conn["id"])
            if line is None:
                continue
            p1_raw = self._from_port_pos(conn["from"]["node_id"])
            p2_raw = self._to_port_pos(conn["to"]["node_id"])
            if p1_raw is None or p2_raw is None:
                continue
            # Snap port positions to grid so BFS produces clean H/V segments
            p1 = QPointF(round(p1_raw.x() / g) * g, round(p1_raw.y() / g) * g)
            p2 = QPointF(round(p2_raw.x() / g) * g, round(p2_raw.y() / g) * g)
            raw_route = conn.get("route", [])
            waypoints = [QPointF(p["x"], p["y"]) for p in raw_route]
            excl = {conn["from"]["node_id"], conn["to"]["node_id"]}
            blocked = self._block_cells(excl)
            visual_pts = self._route_grid(p1, p2, waypoints, blocked)
            line.update_route(visual_pts)

    def update_signal_overlay(self, transactions: dict) -> None:
        """Highlight bus-kind connection lines when bus transactions occurred."""
        has_bus = bool(transactions)
        for line in self._conn_items.values():
            if line.kind() == "bus":
                line.set_active(has_bus)

    def clear_signal_overlay(self) -> None:
        """Remove all signal overlay highlights from connection lines."""
        for line in self._conn_items.values():
            line.set_active(False)

    def export_parts(self) -> list[dict]:
        """Return all canvas nodes as a list of dicts for system.json serialisation."""
        result = []
        for item in self.scene().items():
            if isinstance(item, PartNode):
                pos = item.pos()
                result.append({
                    "node_id": item.node_id(),
                    "part_id": item.part()["id"],
                    "name":    item.part()["name"],
                    "x":       round(pos.x(), 2),
                    "y":       round(pos.y(), 2),
                    "sources": dict(item.sources()),
                })
        return result

    def get_node(self, node_id: str) -> "PartNode | None":
        """Return the PartNode with the given node_id, or None."""
        for item in self.scene().items():
            if isinstance(item, PartNode) and item.node_id() == node_id:
                return item
        return None

    def get_all_nodes(self) -> list:
        """Return all PartNode items currently on the canvas."""
        return [i for i in self.scene().items() if isinstance(i, PartNode)]

    def import_parts(self, parts: list[dict], part_library: dict,
                     *, clear: bool = True) -> None:
        """Restore canvas nodes from a saved parts list.

        part_library maps part_id -> part dict (from load_parts()).
        Unknown part_ids are logged and skipped.
        With clear=True (default) the scene is wiped first and the ID
        counter reset so new nodes won't collide with imported ones.
        """
        if clear:
            self.scene().clear()
            self._node_seq = 0

        max_seq = self._node_seq
        for entry in parts:
            part_id = entry.get("part_id", "")
            part    = part_library.get(part_id)
            if part is None:
                self._log(f"Import: unknown part_id '{part_id}', skipped")
                continue
            node_id = entry.get("node_id", self._next_node_id())
            try:
                seq = int(node_id.split("_")[-1])
                max_seq = max(max_seq, seq)
            except (IndexError, ValueError):
                pass
            raw_src = entry.get("sources")
            sources = raw_src if isinstance(raw_src, dict) else {"asm": None, "hdl": None}
            node = PartNode(part, node_id, sources)
            node.set_snap(self._snap_enabled)
            node._pos_changed_cb = self.update_connections
            node.setPos(QPointF(entry.get("x", 0.0), entry.get("y", 0.0)))
            self.scene().addItem(node)
            self._log(f"Imported: {part['name']}  ({part_id})  [{node_id}]")

        self._node_seq = max_seq

    def add_connection(self, from_node_id: str, from_port: str,
                       to_node_id: str, to_port: str,
                       kind: str = "bus", width: int = 32,
                       label: str = "", route: "list | None" = None,
                       color: str = "") -> dict:
        """Add a logical connection, draw its line, and return the dict."""
        route_data = [{"x": p.x(), "y": p.y()} for p in (route or [])]
        conn = {
            "id":    self._next_conn_id(),
            "from":  {"node_id": from_node_id, "port": from_port},
            "to":    {"node_id": to_node_id,   "port": to_port},
            "kind":  kind,
            "width": width,
            "label": label,
            "route": route_data,
            "color": color,
        }
        self._connections.append(conn)
        self._conn_items[conn["id"]] = self._make_conn_item(conn)
        self.update_connections()
        self._log(f"Connected: {from_node_id}:{from_port} → {to_node_id}:{to_port}")
        return conn

    def export_canvas(self) -> dict:
        """Return parts and connections for system.json serialisation."""
        return {
            "parts":       self.export_parts(),
            "connections": list(self._connections),
        }

    def import_canvas(self, data: dict, part_library: dict,
                      *, clear: bool = True) -> None:
        """Restore canvas from export_canvas() output."""
        if clear:
            self._pending_port = None
            if self._mode == "wire":
                self._cancel_wire()
            self._hide_handles()
            self._conn_items.clear()   # scene.clear() in import_parts removes items
            self._connections = []
            self._conn_seq = 0
        self.import_parts(data.get("parts", []), part_library, clear=clear)
        max_seq = self._conn_seq
        for conn in data.get("connections", []):
            entry = dict(conn)
            conn_id = entry.get("id", "")
            if not conn_id:
                entry["id"] = self._next_conn_id()
            else:
                try:
                    seq = int(conn_id.split("_")[-1])
                    max_seq = max(max_seq, seq)
                except (IndexError, ValueError):
                    pass
            self._connections.append(entry)
        self._conn_seq = max_seq
        self._rebuild_conn_items()

    def set_part_library(self, lib: dict) -> None:
        self._part_library = lib

    def set_snap(self, enabled: bool) -> None:
        self._snap_enabled = enabled
        for item in self.scene().items():
            if isinstance(item, PartNode):
                item.set_snap(enabled)

    def add_part_at(self, part: dict, scene_pos: QPointF) -> None:
        if self._snap_enabled:
            g         = float(GridScene.GRID_SIZE)
            scene_pos = QPointF(round(scene_pos.x() / g) * g,
                                round(scene_pos.y() / g) * g)
        node_id = self._next_node_id()
        node = PartNode(part, node_id)
        node.set_snap(self._snap_enabled)
        node._pos_changed_cb = self.update_connections
        node.setPos(scene_pos)
        self.scene().addItem(node)
        self._log(f"Added: {part['name']}  ({part['id']})  [{node_id}]")

    def add_part(self, part: dict) -> None:
        center = self.mapToScene(self.viewport().rect().center())
        offset = QPointF(self._add_offset * 20, self._add_offset * 20)
        self._add_offset = (self._add_offset + 1) % 8
        self.add_part_at(part, center + offset)

    def zoom_in(self) -> None:
        if self.transform().m11() * 1.25 <= _ZOOM_MAX:
            self.scale(1.25, 1.25)

    def zoom_out(self) -> None:
        if self.transform().m11() * 0.8 >= _ZOOM_MIN:
            self.scale(0.8, 0.8)

    def reset_zoom(self) -> None:
        self.resetTransform()

    def fit_to_view(self) -> None:
        if not self.scene().items():
            return
        self.fitInView(
            self.scene().itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def set_grid_visible(self, enabled: bool) -> None:
        scene = self.scene()
        if isinstance(scene, GridScene):
            scene.set_grid_visible(enabled)

    # ------------------------------------------------------------------ events

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
            event.accept()
        elif delta < 0:
            self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_origin = event.pos()
            self._pan_last   = event.pos()
            self._panned     = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._mode == "wire":
            self._update_wire_preview(self.mapToScene(event.pos()))
        if event.buttons() & Qt.MouseButton.MiddleButton and self._pan_origin is not None:
            total = event.pos() - self._pan_origin
            if not self._panned and total.manhattanLength() > _PAN_THRESHOLD:
                self._panned = True
            if self._panned:
                delta = event.pos() - self._pan_last
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - delta.x()
                )
                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value() - delta.y()
                )
            self._pan_last = event.pos()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self.unsetCursor()
            self._pan_origin = None
            self._pan_last   = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasText():
            event.ignore()
            return
        part_id = event.mimeData().text()
        part = self._part_library.get(part_id)
        if part is None:
            event.ignore()
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        self.add_part_at(part, scene_pos)
        event.acceptProposedAction()

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        # Resolve PortDot hit to its parent PartNode
        if isinstance(item, PortDot):
            item = item.parentItem()

        scene_pos = self.mapToScene(event.pos())

        # Wire mode
        if self._mode == "wire":
            if isinstance(item, PartNode):
                menu = QMenu(self)
                menu.addAction("ここに接続")
                menu.addAction("キャンセル")
                chosen = menu.exec(event.globalPos())
                if chosen is None:
                    return
                if chosen.text() == "ここに接続":
                    self._finish_wire(item.node_id(), "bus")
                else:
                    self._cancel_wire()
            else:
                self._add_waypoint(scene_pos)
            return

        # Design mode
        if not isinstance(item, PartNode):
            super().contextMenuEvent(event)
            return

        name = item.part()["name"]
        menu = QMenu(self)
        menu.addAction("接続を開始")
        menu.addSeparator()
        menu.addAction("プログラムを開く")
        menu.addAction("HDLを開く")
        menu.addSeparator()
        menu.addAction("設定")
        menu.addAction("信号を見る")
        menu.addAction("メモリを見る")
        menu.addSeparator()
        menu.addAction("複製")
        menu.addAction("削除")

        chosen = menu.exec(event.globalPos())
        if chosen is None:
            return

        label = chosen.text()
        self._log(f"Node Action: {label} - {name}")

        if label == "接続を開始":
            self._start_wire(item.node_id(), "bus")
        elif label == "削除":
            self.scene().removeItem(item)
        elif label == "複製":
            new_id = self._next_node_id()
            clone = PartNode(item.part(), new_id)
            clone._pos_changed_cb = self.update_connections
            clone.setPos(item.pos() + QPointF(20, 20))
            self.scene().addItem(clone)
        elif label == "プログラムを開く":
            self.tab_open_requested.emit(item.part(), item.node_id(), "asm")
        elif label == "HDLを開く":
            self.tab_open_requested.emit(item.part(), item.node_id(), "v")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene().selectedItems():
                if isinstance(item, PartNode):
                    self._log(
                        f"Removed: {item.part()['name']}  ({item.part()['id']})"
                        f"  [{item.node_id()}]"
                    )
                    self.scene().removeItem(item)
        else:
            super().keyPressEvent(event)
