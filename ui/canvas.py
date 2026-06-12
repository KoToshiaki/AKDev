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

# Visual port layout (PATCH_WIRING_PORTS_V05): margin from edge start + stack spacing.
_VP_MARGIN  = 12.0
_VP_SPACING = 16.0
_VP_RADIUS  = 5.0
# Node bounding-rect padding so edge-drawn visual port dots stay inside the item
# (otherwise moving a node leaves "ghost" dots at the old position).
_NODE_PAD   = _VP_RADIUS + 3.0

# Outward direction per port side, for curved wire control points.
_SIDE_DIR = {"right": (1.0, 0.0), "left": (-1.0, 0.0),
             "top": (0.0, -1.0), "bottom": (0.0, 1.0)}


def _side_dir(side: str) -> tuple:
    return _SIDE_DIR.get(side, (1.0, 0.0))

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
_DROP_HL_COLOR      = "#3B82F6"   # accent outline for port-drag drop candidate
_WIRE_SELECT_COLOR  = "#ffffff"   # selected wire highlight (strongest)
_PORT_MOVE_COLOR    = "#ffdd33"   # ring around a visual port being moved (Alt+drag)

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
        # B3: origin crosshair — always drawn (even when the grid is off) so an
        # otherwise empty canvas still reads as "loaded" and panning is visible.
        if rect.left() <= 0 <= rect.right() and rect.top() <= 0 <= rect.bottom():
            painter.setPen(QPen(QColor(150, 170, 200), 0.0))
            painter.drawLine(QPointF(-14.0, 0.0), QPointF(14.0, 0.0))
            painter.drawLine(QPointF(0.0, -14.0), QPointF(0.0, 14.0))
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
        self._active   = False
        self._hovered  = False
        self._selected = False
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

    def _apply_pen(self) -> None:
        """Resolve the pen from selected/active/hover state.

        Priority: selected > active > hover > base, so a selected wire stays
        clearly marked even when a signal overlay (active) is also lit.
        """
        if self._selected:
            self.setPen(QPen(QColor(_WIRE_SELECT_COLOR), self._base_pen.widthF() + 2.5))
        elif self._active:
            bright = self._base_pen.color().lighter(160)
            self.setPen(QPen(bright, self._base_pen.widthF() + 1.5))
        elif self._hovered:
            bright = self._base_pen.color().lighter(140)
            self.setPen(QPen(bright, self._base_pen.widthF() + 1.0))
        else:
            self.setPen(self._base_pen)

    def set_active(self, active: bool) -> None:
        """Highlight the line when active (bus transaction occurred)."""
        self._active = bool(active)
        self._apply_pen()

    def set_hovered(self, hovered: bool) -> None:
        """Highlight the line on mouse hover (subtler than active)."""
        self._hovered = bool(hovered)
        self._apply_pen()

    def is_hovered(self) -> bool:
        return self._hovered

    def set_selected(self, selected: bool) -> None:
        """Mark the line as the selected wire (strongest highlight)."""
        self._selected = bool(selected)
        self._apply_pen()

    def is_selected(self) -> bool:
        return self._selected

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

    def update_curve(self, p1: QPointF, p2: QPointF,
                     from_side: str = "right", to_side: str = "left") -> None:
        """Draw a cubic-bezier wire that leaves each port along its outward side.

        Used for Dynamic Visual Port connections so wires flow naturally from the
        ports instead of following grid/Manhattan routing.
        """
        d1 = _side_dir(from_side)
        d2 = _side_dir(to_side)
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = (dx * dx + dy * dy) ** 0.5
        k = max(40.0, dist * 0.4)
        c1 = QPointF(p1.x() + d1[0] * k, p1.y() + d1[1] * k)
        c2 = QPointF(p2.x() + d2[0] * k, p2.y() + d2[1] * k)
        path = QPainterPath(p1)
        path.cubicTo(c1, c2, p2)
        self.setPath(path)


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
        self._color: str      = ""     # instance color override ("" = category default)
        self._pos_changed_cb  = None   # called by Canvas after position changes
        self._sources: dict = (
            sources if sources is not None else {"asm": None, "hdl": None}
        )
        # Dynamic Visual Ports (PATCH_WIRING_PORTS_V05): created on connect; 0 initially.
        self._visual_ports: list[dict] = []
        # Hover feedback (PATCH_WIRE_HOVER_FEEDBACK_V05): transient display-only state.
        self._hover_vp_id: "str | None" = None   # visual port under the cursor
        self._drop_highlight: bool      = False  # port-drag connect candidate
        # Visual port move (PATCH_VISUAL_PORT_MOVE_V05): vp currently being dragged.
        self._moving_vp_id: "str | None" = None
        # Legacy single port dot: kept for sim/_on_port_click + existing tests, but
        # HIDDEN on the canvas so parts show 0 visible ports until wired.
        self._port_dot = PortDot(node_id, "bus", self)
        self._port_dot.setPos(_NODE_W, _NODE_H / 2)
        self._port_dot.setVisible(False)
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

    def set_color(self, color: str) -> bool:
        """Set an instance color override. Empty string reverts to category color.

        Returns True if applied (valid color or cleared), False if rejected.
        """
        if color and not QColor(color).isValid():
            return False
        self._color = color
        self.update()
        return True

    def color(self) -> str:
        """Return the instance color override ("" when using the category color)."""
        return self._color

    # -------------------------------------------------- visual ports (PATCH_WIRING_PORTS_V05)

    def visual_ports(self) -> list:
        return self._visual_ports

    def add_visual_port(self, vp: dict) -> None:
        self._visual_ports.append(vp)
        self.update()

    def get_visual_port(self, vp_id: str) -> "dict | None":
        for vp in self._visual_ports:
            if vp.get("id") == vp_id:
                return vp
        return None

    def remove_visual_port(self, vp_id: str) -> None:
        self._visual_ports = [vp for vp in self._visual_ports if vp.get("id") != vp_id]
        self.update()

    def set_visual_ports(self, vps: list) -> None:
        self._visual_ports = list(vps)
        self.update()

    def _vp_local(self, vp: dict) -> QPointF:
        """Local (item-space) point for a visual port on its side at its offset."""
        side = vp.get("side", "right")
        off  = float(vp.get("offset", _NODE_H / 2))
        if side == "left":
            return QPointF(0.0, off)
        if side == "top":
            return QPointF(off, 0.0)
        if side == "bottom":
            return QPointF(off, _NODE_H)
        return QPointF(_NODE_W, off)   # right (default)

    def visual_port_pos(self, vp_id: str) -> "QPointF | None":
        """Scene position of a visual port, or None if it does not exist."""
        vp = self.get_visual_port(vp_id)
        if vp is None:
            return None
        return self.pos() + self._vp_local(vp)

    def node_size(self) -> tuple:
        """Return the node's (width, height). Fixed for now; future-proof hook."""
        return (_NODE_W, _NODE_H)

    def edge_from_local(self, local: QPointF) -> tuple:
        """Map a local (item-space) point to the nearest edge (side, offset).

        offset is the distance along that edge, clamped to the node size, so a
        visual port stays constrained to the part's border (no free scene coords).
        """
        w, h = self.node_size()
        x = max(0.0, min(local.x(), float(w)))
        y = max(0.0, min(local.y(), float(h)))
        d_left, d_right, d_top, d_bottom = x, w - x, y, h - y
        m = min(d_left, d_right, d_top, d_bottom)
        if m == d_left:
            return ("left", round(y, 2))
        if m == d_right:
            return ("right", round(y, 2))
        if m == d_top:
            return ("top", round(x, 2))
        return ("bottom", round(x, 2))

    def set_moving_port(self, vp_id: "str | None") -> None:
        """Mark a visual port as being moved (None = none). Repaints on change."""
        if vp_id == self._moving_vp_id:
            return
        self._moving_vp_id = vp_id
        self.update()

    def moving_port(self) -> "str | None":
        return self._moving_vp_id

    # -------------------------------------------------- hover feedback (PATCH_WIRE_HOVER_FEEDBACK_V05)

    def set_hover_port(self, vp_id: "str | None") -> None:
        """Mark a visual port as hovered (None = none). Repaints on change."""
        if vp_id == self._hover_vp_id:
            return
        self._hover_vp_id = vp_id
        self.update()

    def hover_port(self) -> "str | None":
        return self._hover_vp_id

    def set_drop_highlight(self, enabled: bool) -> None:
        """Highlight this node as a port-drag connection candidate. Repaints on change."""
        enabled = bool(enabled)
        if enabled == self._drop_highlight:
            return
        self._drop_highlight = enabled
        self.update()

    def drop_highlight(self) -> bool:
        return self._drop_highlight

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
        # Padded so edge-drawn visual port dots are inside the item's bounds;
        # otherwise moving the node leaves ghost dots at the old position (bug 1).
        return QRectF(-_NODE_PAD, -_NODE_PAD,
                      _NODE_W + 2 * _NODE_PAD, _NODE_H + 2 * _NODE_PAD)

    def paint(self, painter, option, widget=None):
        # instance_color override (PATCH_PART_VISUAL_V05) wins over the category color.
        if self._color and QColor(self._color).isValid():
            fill = QColor(self._color)
        else:
            fill = _CAT_COLOR.get(self._part.get("category", ""), _DEFAULT_COLOR)
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

        # Visual ports (created on connect) — drawn as small kind-colored dots.
        # Priority: moving (Alt-drag) > hovered > normal.
        for vp in self._visual_ports:
            col = QColor(_KIND_COLORS.get(vp.get("kind", "bus"), "#aaaaaa"))
            vpid = vp.get("id")
            if vpid == self._moving_vp_id:
                painter.setPen(QPen(QColor(_PORT_MOVE_COLOR), 2.5))
                painter.setBrush(QBrush(col.lighter(160)))
                painter.drawEllipse(self._vp_local(vp), 8.0, 8.0)
            elif vpid == self._hover_vp_id:
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.setBrush(QBrush(col.lighter(140)))
                painter.drawEllipse(self._vp_local(vp), 7.0, 7.0)
            else:
                painter.setPen(QPen(QColor("#333333"), 1))
                painter.setBrush(QBrush(col))
                painter.drawEllipse(self._vp_local(vp), 5.0, 5.0)

        # Port-drag drop candidate — accent outline drawn on top.
        if self._drop_highlight:
            painter.setPen(QPen(QColor(_DROP_HL_COLOR), 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(-3, -3, _NODE_W + 6, _NODE_H + 6, 8, 8)


class Canvas(QGraphicsView):
    """Main system canvas — hosts PartNode items."""

    selection_changed  = Signal(list)              # list[PartNode]
    tab_open_requested = Signal(dict, str, str)   # (part, node_id, ext)
    mode_changed       = Signal(str)              # "wire" | "design"

    def __init__(self, log_fn=None):
        super().__init__()
        self.setScene(GridScene(self))
        # B3: give the scene a generous fixed extent so middle-button pan has
        # scroll range even on an empty canvas (otherwise nothing moves and it
        # looks frozen / unloaded).
        self.setSceneRect(-2000.0, -2000.0, 4000.0, 4000.0)
        self._log            = log_fn or (lambda s: None)
        self._node_seq       = 0
        self._conn_seq:    int        = 0
        self._vp_seq:      int        = 0    # visual port id sequence
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
        # Port-drag connect (PATCH_PORT_DRAG_CONNECT_V05): drag from a visual port.
        self._port_drag: "dict | None"      = None    # {node_id, vp_id, logical_port, side}
        self._port_drag_preview: "QGraphicsPathItem | None" = None
        # Hover feedback (PATCH_WIRE_HOVER_FEEDBACK_V05): display-only transient state.
        self._hover_vp:            "dict | None" = None   # {"node_id", "vp_id"}
        self._hover_conn_id:       "str | None"  = None   # hovered ConnectionLine id
        self._hover_drop_node_id:  "str | None"  = None   # port-drag drop candidate
        # Wire selection (PATCH_WIRE_SELECT_DELETE_V05): independent of hover.
        self._selected_conn_id:    "str | None"  = None   # selected ConnectionLine id
        # Visual port move (PATCH_VISUAL_PORT_MOVE_V05): Alt+drag a vp along an edge.
        self._port_move: "dict | None" = None  # {node_id, vp_id, original/current side+offset}
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

    def _next_vp_id(self) -> str:
        self._vp_seq += 1
        return f"vp_{self._vp_seq:04d}"

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
        """Enter wire mode starting from node_id:port_name (delegates to begin)."""
        self._begin_wire_from(node_id, port_name)

    def _begin_wire_from(self, node_id: str, port_name: str) -> None:
        """Set the wire start point and enter the 'drawing' sub-state.

        Works whether the canvas was already armed (mode == 'wire', no start)
        or in design mode. Centralises start-point setup so the ribbon toggle
        and the right-click "start from here" path behave identically.
        """
        self._mode = "wire"
        self._wire_from = {"node_id": node_id, "port_name": port_name}
        self._wire_waypoints = []
        # Replace any stale preview.
        if self._wire_preview is not None and self._wire_preview.scene() is not None:
            self.scene().removeItem(self._wire_preview)
        preview = QGraphicsPathItem()
        preview.setPen(QPen(_WIRE_PREVIEW_COLOR, 1.5, Qt.PenStyle.DashLine))
        preview.setZValue(-0.5)
        self.scene().addItem(preview)
        self._wire_preview = preview
        self._show_handles()
        self._refresh_wire_decoration()
        self.mode_changed.emit("wire")

    def _add_waypoint(self, scene_pos: QPointF) -> None:
        """Snap scene_pos to grid and append as a wire waypoint."""
        g = float(GridScene.GRID_SIZE)
        snapped = QPointF(round(scene_pos.x() / g) * g,
                          round(scene_pos.y() / g) * g)
        self._wire_waypoints.append(snapped)

    def _finish_wire(self, to_node_id: str, to_port_name: str) -> None:
        """Complete the in-progress wire: create visual ports + a connection."""
        if self._wire_from is None:
            return
        from_info = self._wire_from
        waypoints = list(self._wire_waypoints)
        self._cancel_wire()
        # Dynamic Visual Port: create a contact point on each endpoint node.
        from_vp = self._create_visual_port(from_info["node_id"], "right",
                                           from_info["port_name"])
        to_vp = self._create_visual_port(to_node_id, "left", to_port_name)
        self.add_connection(
            from_info["node_id"], from_info["port_name"],
            to_node_id, to_port_name,
            route=waypoints,
            from_vp=(from_vp["id"] if from_vp else None),
            to_vp=(to_vp["id"] if to_vp else None),
        )

    def _create_visual_port(self, node_id: str, side: str,
                            logical_port: str, kind: str = "") -> "dict | None":
        """Create a visual port on a node's edge (stacked to avoid overlap)."""
        node = self.get_node(node_id)
        if node is None:
            return None
        kind = kind or logical_port or "bus"
        length = _NODE_H if side in ("left", "right") else _NODE_W
        existing = [vp for vp in node.visual_ports() if vp.get("side") == side]
        offset = _VP_MARGIN + len(existing) * _VP_SPACING
        if offset > length - _VP_MARGIN:
            offset = length / 2
        vp = {
            "id":     self._next_vp_id(),
            "side":   side,
            "offset": round(offset, 2),
            "kind":   kind,
            "label":  logical_port,
            "locked": False,
        }
        node.add_visual_port(vp)
        return vp

    def set_visual_port_offset(self, node_id: str, vp_id: str, offset: float) -> bool:
        """Move a visual port along its edge (rejected if locked)."""
        node = self.get_node(node_id)
        if node is None:
            return False
        vp = node.get_visual_port(vp_id)
        if vp is None or vp.get("locked"):
            return False
        length = _NODE_H if vp.get("side") in ("left", "right") else _NODE_W
        vp["offset"] = round(max(0.0, min(float(offset), length)), 2)
        node.update()
        self.update_connections()
        return True

    def set_visual_port_side(self, node_id: str, vp_id: str, side: str) -> bool:
        """Move a visual port to a different edge (rejected if locked)."""
        if side not in ("left", "right", "top", "bottom"):
            return False
        node = self.get_node(node_id)
        if node is None:
            return False
        vp = node.get_visual_port(vp_id)
        if vp is None or vp.get("locked"):
            return False
        vp["side"] = side
        node.update()
        self.update_connections()
        return True

    def arrange_visual_ports(self, node_id: str) -> bool:
        """Evenly distribute visual ports along each edge (locked ports kept)."""
        node = self.get_node(node_id)
        if node is None:
            return False
        changed = False
        for side in ("left", "right", "top", "bottom"):
            ports = [vp for vp in node.visual_ports()
                     if vp.get("side") == side and not vp.get("locked")]
            n = len(ports)
            if n == 0:
                continue
            length = _NODE_H if side in ("left", "right") else _NODE_W
            for i, vp in enumerate(ports):
                vp["offset"] = round(length * (i + 1) / (n + 1), 2)
                changed = True
        if changed:
            node.update()
            self.update_connections()
        return changed

    def _prune_orphan_visual_ports(self) -> None:
        """Remove visual ports not referenced by any connection."""
        referenced = set()
        for conn in self._connections:
            for side in ("from", "to"):
                vp_id = conn.get(side, {}).get("visual_port_id")
                if vp_id:
                    referenced.add(vp_id)
        for node in self.get_all_nodes():
            for vp in list(node.visual_ports()):
                if vp.get("id") not in referenced:
                    node.remove_visual_port(vp["id"])

    def _cancel_wire(self) -> None:
        """Abort wire mode, clearing preview / waypoints / handles / pending."""
        if self._wire_preview is not None and self._wire_preview.scene() is not None:
            self.scene().removeItem(self._wire_preview)
        self._wire_preview = None
        self._wire_from = None
        self._wire_waypoints = []
        self._pending_port = None
        self._hide_handles()
        self._mode = "design"
        self._refresh_wire_decoration()
        self.mode_changed.emit("design")

    def _refresh_wire_decoration(self) -> None:
        """Light visual cue: tint the Canvas frame while in wire mode."""
        if self._mode == "wire":
            self.setStyleSheet(
                "QGraphicsView { border: 2px solid %s; }" % _WIRE_PREVIEW_COLOR.name()
            )
        else:
            self.setStyleSheet("")

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

    # ------------------------------------------ port-drag connect (PATCH_PORT_DRAG_CONNECT_V05)

    def _visual_port_at(self, scene_pos: QPointF) -> "tuple | None":
        """Return (PartNode, vp dict) whose visual port is near scene_pos, else None."""
        slack = _VP_RADIUS + 4.0
        for node in self.get_all_nodes():
            for vp in node.visual_ports():
                p = node.visual_port_pos(vp["id"])
                if p is None:
                    continue
                if abs(p.x() - scene_pos.x()) <= slack and abs(p.y() - scene_pos.y()) <= slack:
                    return (node, vp)
        return None

    def _connection_at(self, scene_pos: QPointF, slack: float = 6.0) -> "ConnectionLine | None":
        """Return the ConnectionLine whose path passes near scene_pos, else None."""
        for item in self._conn_items.values():
            path = item.path()
            if path.isEmpty():
                continue
            for i in range(25):
                pt = path.pointAtPercent(i / 24.0)
                if (abs(pt.x() - scene_pos.x()) <= slack
                        and abs(pt.y() - scene_pos.y()) <= slack):
                    return item
        return None

    # -------------------------------------------------- hover feedback (PATCH_WIRE_HOVER_FEEDBACK_V05)

    def _set_hover_vp(self, node: "PartNode", vp: dict) -> None:
        """Mark (node, vp) as the hovered visual port."""
        if (self._hover_vp is not None
                and self._hover_vp["node_id"] == node.node_id()
                and self._hover_vp["vp_id"] == vp["id"]):
            return
        self._clear_hover_vp()
        node.set_hover_port(vp["id"])
        self._hover_vp = {"node_id": node.node_id(), "vp_id": vp["id"]}

    def _clear_hover_vp(self) -> None:
        if self._hover_vp is None:
            return
        node = self.get_node(self._hover_vp["node_id"])
        if node is not None:
            node.set_hover_port(None)
        self._hover_vp = None

    def _set_hover_conn(self, conn_id: "str | None") -> None:
        """Mark a ConnectionLine (by id) as hovered; None clears."""
        if conn_id == self._hover_conn_id:
            return
        old = self._conn_items.get(self._hover_conn_id)
        if old is not None:
            old.set_hovered(False)
        new = self._conn_items.get(conn_id)
        if new is not None:
            new.set_hovered(True)
        self._hover_conn_id = conn_id

    # -------------------------------------------------- wire selection (PATCH_WIRE_SELECT_DELETE_V05)

    def _set_selected_conn(self, conn_id: "str | None") -> None:
        """Select a ConnectionLine (by id); None clears. Independent of hover."""
        if conn_id == self._selected_conn_id:
            return
        old = self._conn_items.get(self._selected_conn_id)
        if old is not None:
            old.set_selected(False)
        new = self._conn_items.get(conn_id)
        if new is not None:
            new.set_selected(True)
        self._selected_conn_id = conn_id

    def selected_conn_id(self) -> "str | None":
        return self._selected_conn_id

    def _remove_connection(self, conn_id: str) -> bool:
        """Single source of truth for removing one connection (data + line item).

        Clears selection/hover pointing at it, prunes only orphaned visual ports
        (shared fan-out ports referenced by other connections are kept), and
        refreshes the remaining wires. Returns True if a connection was removed.
        """
        if not any(c["id"] == conn_id for c in self._connections):
            return False
        if self._selected_conn_id == conn_id:
            self._selected_conn_id = None
        if self._hover_conn_id == conn_id:
            self._hover_conn_id = None
        line = self._conn_items.pop(conn_id, None)
        if line is not None and line.scene() is not None:
            self.scene().removeItem(line)
        self._connections = [c for c in self._connections if c["id"] != conn_id]
        self._prune_orphan_visual_ports()
        self.update_connections()
        self._log(f"Removed wire [{conn_id}]")
        return True

    def _update_hover(self, scene_pos: QPointF) -> None:
        """Refresh visual-port / wire hover from a scene position (no drag active)."""
        hit = self._visual_port_at(scene_pos)
        if hit is not None:
            self._set_hover_vp(hit[0], hit[1])
            self._set_hover_conn(None)   # a port takes priority over a wire underneath
            return
        self._clear_hover_vp()
        conn = self._connection_at(scene_pos)
        self._set_hover_conn(conn.conn_id() if conn is not None else None)

    def _set_drop_highlight(self, node_id: "str | None") -> None:
        """Highlight node_id as the port-drag drop candidate; None clears."""
        if node_id == self._hover_drop_node_id:
            return
        old = self.get_node(self._hover_drop_node_id) if self._hover_drop_node_id else None
        if old is not None:
            old.set_drop_highlight(False)
        new = self.get_node(node_id) if node_id else None
        if new is not None:
            new.set_drop_highlight(True)
        self._hover_drop_node_id = node_id

    def _update_drop_target(self, node_id: "str | None") -> None:
        """Set the drop candidate, excluding the port-drag source (same part)."""
        if self._port_drag is None:
            self._set_drop_highlight(None)
            return
        if node_id == self._port_drag.get("node_id"):
            node_id = None   # cannot connect a part to itself
        self._set_drop_highlight(node_id)

    def _start_port_drag(self, node: "PartNode", vp: dict) -> None:
        """Begin dragging a new wire out of an existing visual port."""
        self._cancel_port_drag()
        self._log("Wire: drag to another part to connect")
        self._port_drag = {
            "node_id":      node.node_id(),
            "vp_id":        vp["id"],
            "logical_port": vp.get("label", "bus"),
            "side":         vp.get("side", "right"),
        }
        preview = QGraphicsPathItem()
        preview.setPen(QPen(_WIRE_PREVIEW_COLOR, 1.5, Qt.PenStyle.DashLine))
        preview.setZValue(-0.5)
        self.scene().addItem(preview)
        self._port_drag_preview = preview

    def _update_port_drag_preview(self, cursor_scene_pos: QPointF) -> None:
        """Redraw the dashed curved preview from the source port to the cursor."""
        if self._port_drag is None or self._port_drag_preview is None:
            return
        node = self.get_node(self._port_drag["node_id"])
        if node is None:
            return
        src = node.visual_port_pos(self._port_drag["vp_id"])
        if src is None:
            return
        d = _side_dir(self._port_drag["side"])
        dx = cursor_scene_pos.x() - src.x()
        dy = cursor_scene_pos.y() - src.y()
        k = max(40.0, (dx * dx + dy * dy) ** 0.5 * 0.4)
        c1 = QPointF(src.x() + d[0] * k, src.y() + d[1] * k)
        c2 = QPointF(cursor_scene_pos.x() - d[0] * k, cursor_scene_pos.y() - d[1] * k)
        path = QPainterPath(src)
        path.cubicTo(c1, c2, cursor_scene_pos)
        self._port_drag_preview.setPath(path)

    def _finish_port_drag(self, to_node_id: "str | None") -> bool:
        """Complete a port drag onto to_node_id. Returns True if a wire was made."""
        src = self._port_drag
        self._cancel_port_drag()
        if src is None or not to_node_id or to_node_id == src["node_id"]:
            return False
        if self.get_node(to_node_id) is None:
            return False
        to_vp = self._create_visual_port(to_node_id, "left", src["logical_port"])
        self.add_connection(
            src["node_id"], src["logical_port"],
            to_node_id, src["logical_port"],
            from_vp=src["vp_id"],
            to_vp=(to_vp["id"] if to_vp else None),
        )
        return True

    def _cancel_port_drag(self) -> None:
        """Abort a port drag, removing the preview and any drop highlight."""
        if (self._port_drag_preview is not None
                and self._port_drag_preview.scene() is not None):
            self.scene().removeItem(self._port_drag_preview)
        self._port_drag_preview = None
        self._port_drag = None
        self._set_drop_highlight(None)

    # ------------------------------------------ visual port move (PATCH_VISUAL_PORT_MOVE_V05)

    def _start_port_move(self, node: "PartNode", vp: dict) -> bool:
        """Begin an Alt+drag move of a visual port. Rejected if locked. Returns True if started."""
        if vp.get("locked"):
            self._log("Visual port is locked")
            return False
        self._cancel_port_drag()   # ensure a port-drag connect is not also active
        side   = vp.get("side", "right")
        offset = float(vp.get("offset", 0.0))
        self._port_move = {
            "node_id":         node.node_id(),
            "vp_id":           vp["id"],
            "original_side":   side,
            "original_offset": offset,
            "current_side":    side,
            "current_offset":  offset,
        }
        node.set_moving_port(vp["id"])
        self._log("Visual port: drag to move along the part edge")
        return True

    def _update_port_move(self, scene_pos: QPointF) -> None:
        """Constrain the moving visual port to the nearest edge under the cursor."""
        if self._port_move is None:
            return
        node = self.get_node(self._port_move["node_id"])
        if node is None:
            return
        vp = node.get_visual_port(self._port_move["vp_id"])
        if vp is None or vp.get("locked"):
            return
        side, offset = node.edge_from_local(node.mapFromScene(scene_pos))
        vp["side"]   = side
        vp["offset"] = offset
        self._port_move["current_side"]   = side
        self._port_move["current_offset"] = offset
        node.update()
        self.update_connections()   # wires follow the new endpoint (incl. fan-out)

    def _finish_port_move(self) -> bool:
        """Confirm the visual port move at its current edge position."""
        if self._port_move is None:
            return False
        pm = self._port_move
        node = self.get_node(pm["node_id"])
        if node is not None:
            node.set_moving_port(None)
        self._port_move = None
        if (pm["current_side"] != pm["original_side"]
                or pm["current_offset"] != pm["original_offset"]):
            self._log(
                f"Visual port moved: [{pm['vp_id']}] -> "
                f"{pm['current_side']} @ {pm['current_offset']}"
            )
        return True

    def _cancel_port_move(self) -> None:
        """Abort a visual port move, restoring its original side/offset."""
        if self._port_move is None:
            return
        pm = self._port_move
        node = self.get_node(pm["node_id"])
        if node is not None:
            vp = node.get_visual_port(pm["vp_id"])
            if vp is not None:
                vp["side"]   = pm["original_side"]
                vp["offset"] = pm["original_offset"]
            node.set_moving_port(None)
            node.update()
        self._port_move = None
        self.update_connections()

    # ------------------------------------------------------------------ public

    def set_mode(self, mode: str) -> None:
        """Switch canvas mode. 'design' cancels any active wire state."""
        if mode == self._mode:
            return
        if mode == "design":
            self._cancel_wire()  # sets _mode, hides handles, clears decoration, emits
        else:
            # Armed: wire mode without a start point yet.
            self._mode = "wire"
            self._show_handles()
            self._refresh_wire_decoration()
            self.mode_changed.emit("wire")

    def _conn_endpoint(self, side: dict, fallback_fn) -> "QPointF | None":
        """Resolve a connection endpoint: visual port pos if set, else node edge."""
        node_id = side.get("node_id")
        vp_id = side.get("visual_port_id")
        if vp_id:
            node = self.get_node(node_id)
            if node is not None:
                pos = node.visual_port_pos(vp_id)
                if pos is not None:
                    return pos
        return fallback_fn(node_id)

    def _is_dynamic_conn(self, conn: dict) -> bool:
        """True if the connection uses Dynamic Visual Ports (→ curved wire)."""
        return bool(conn.get("from", {}).get("visual_port_id")
                    or conn.get("to", {}).get("visual_port_id"))

    def _vp_side(self, side: dict) -> "str | None":
        """Side of the visual port referenced by a connection endpoint, if any."""
        vp_id = side.get("visual_port_id")
        if not vp_id:
            return None
        node = self.get_node(side.get("node_id"))
        if node is None:
            return None
        vp = node.get_visual_port(vp_id)
        return vp.get("side") if vp else None

    def update_connections(self) -> None:
        """Refresh connection lines.

        Dynamic Visual Port connections are drawn as curved wires that leave
        their ports naturally; legacy (port-less) connections keep the
        obstacle-aware grid/Manhattan routing for backward compatibility.
        """
        g = float(GridScene.GRID_SIZE)
        for conn in self._connections:
            line = self._conn_items.get(conn["id"])
            if line is None:
                continue
            p1_raw = self._conn_endpoint(conn["from"], self._from_port_pos)
            p2_raw = self._conn_endpoint(conn["to"], self._to_port_pos)
            if p1_raw is None or p2_raw is None:
                continue
            # Dynamic Visual Port connections → curved wire (no grid routing).
            if self._is_dynamic_conn(conn):
                s1 = self._vp_side(conn["from"]) or "right"
                s2 = self._vp_side(conn["to"]) or "left"
                line.update_curve(p1_raw, p2_raw, s1, s2)
                continue
            # Snap port positions to grid so BFS produces clean H/V segments
            p1 = QPointF(round(p1_raw.x() / g) * g, round(p1_raw.y() / g) * g)
            p2 = QPointF(round(p2_raw.x() / g) * g, round(p2_raw.y() / g) * g)
            raw_route = conn.get("route", [])
            waypoints = [QPointF(p["x"], p["y"]) for p in raw_route]
            excl = {conn["from"]["node_id"], conn["to"]["node_id"]}
            blocked = self._block_cells(excl)
            visual_pts = self._route_grid(p1, p2, waypoints, blocked)
            # B2: the BFS body stays on the grid, but the wire's two endpoints
            # must sit exactly on the real ports so there is no visible gap for
            # non-snapped parts.
            if visual_pts:
                visual_pts[0]  = p1_raw
                visual_pts[-1] = p2_raw
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

    def set_node_color(self, node_id: str, color: str) -> bool:
        """Apply an instance color to a node (PATCH_PART_VISUAL_V05). "" = default."""
        node = self.get_node(node_id)
        if node is None:
            return False
        if not node.set_color(color):
            return False
        self._log(
            f"Color: [{node_id}] -> {color}" if color
            else f"Color: [{node_id}] -> default"
        )
        return True

    def export_parts(self) -> list[dict]:
        """Return all canvas nodes as a list of dicts for system.json serialisation."""
        result = []
        for item in self.scene().items():
            if isinstance(item, PartNode):
                pos = item.pos()
                entry = {
                    "node_id": item.node_id(),
                    "part_id": item.part()["id"],
                    "name":    item.part()["name"],
                    "x":       round(pos.x(), 2),
                    "y":       round(pos.y(), 2),
                    "sources": dict(item.sources()),
                }
                if item.color():
                    entry["instance_color"] = item.color()
                if item.visual_ports():
                    entry["visual_ports"] = [dict(vp) for vp in item.visual_ports()]
                result.append(entry)
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
            self._vp_seq = 0

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
            inst_color = entry.get("instance_color", "")
            if inst_color:
                node.set_color(inst_color)
            vps = entry.get("visual_ports")
            if isinstance(vps, list):
                node.set_visual_ports([dict(vp) for vp in vps])
                for vp in vps:
                    try:
                        seq = int(str(vp.get("id", "")).split("_")[-1])
                        self._vp_seq = max(self._vp_seq, seq)
                    except (IndexError, ValueError):
                        pass
            self.scene().addItem(node)
            self._log(f"Imported: {part['name']}  ({part_id})  [{node_id}]")

        self._node_seq = max_seq

    def add_connection(self, from_node_id: str, from_port: str,
                       to_node_id: str, to_port: str,
                       kind: str = "bus", width: int = 32,
                       label: str = "", route: "list | None" = None,
                       color: str = "",
                       from_vp: "str | None" = None,
                       to_vp: "str | None" = None) -> dict:
        """Add a logical connection, draw its line, and return the dict.

        from_vp / to_vp link the endpoints to Dynamic Visual Ports. The legacy
        `port` key is kept for backward compatibility.
        """
        route_data = [{"x": p.x(), "y": p.y()} for p in (route or [])]
        from_d = {"node_id": from_node_id, "port": from_port}
        to_d   = {"node_id": to_node_id,   "port": to_port}
        if from_vp:
            from_d["visual_port_id"] = from_vp
            from_d["logical_port"]   = from_port
        if to_vp:
            to_d["visual_port_id"] = to_vp
            to_d["logical_port"]   = to_port
        conn = {
            "id":    self._next_conn_id(),
            "from":  from_d,
            "to":    to_d,
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
            # Reset wire/hover selection that referenced the cleared canvas.
            self._selected_conn_id = None
            self._hover_conn_id = None
            self._hover_vp = None
            self._hover_drop_node_id = None
            self._port_move = None
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

    def center_origin(self) -> None:
        """B3: center the view on the origin so the canvas reads as loaded."""
        self.centerOn(0.0, 0.0)

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
        # Left press on a visual port: Alt = move the port, otherwise port-drag connect.
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            hit = self._visual_port_at(scene_pos)
            if hit is not None:
                if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    self._start_port_move(hit[0], hit[1])   # no-op (logged) if locked
                else:
                    self._start_port_drag(hit[0], hit[1])
                event.accept()
                return
            # Design mode: clicking a wire (and not a node) selects it.
            if self._mode == "design":
                item = self.itemAt(event.pos())
                if isinstance(item, PortDot):
                    item = item.parentItem()
                if not isinstance(item, PartNode):
                    conn = self._connection_at(scene_pos)
                    if conn is not None:
                        self._set_selected_conn(conn.conn_id())
                        event.accept()
                        return
                # Blank or node click → wire selection is cleared (node selection
                # is handled by the base class).
                self._set_selected_conn(None)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._port_move is not None:
            self._update_port_move(self.mapToScene(event.pos()))
            event.accept()
            return
        if self._port_drag is not None:
            self._update_port_drag_preview(self.mapToScene(event.pos()))
            item = self.itemAt(event.pos())
            if isinstance(item, PortDot):
                item = item.parentItem()
            self._update_drop_target(item.node_id() if isinstance(item, PartNode) else None)
            event.accept()
            return
        if self._mode == "wire":
            self._update_wire_preview(self.mapToScene(event.pos()))
        # Hover feedback only when no button is held (true mouse hover).
        if event.buttons() == Qt.MouseButton.NoButton:
            self._update_hover(self.mapToScene(event.pos()))
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
        if self._port_move is not None and event.button() == Qt.MouseButton.LeftButton:
            self._finish_port_move()
            event.accept()
            return
        if self._port_drag is not None and event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, PortDot):
                item = item.parentItem()
            to_node_id = item.node_id() if isinstance(item, PartNode) else None
            self._finish_port_drag(to_node_id)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:
        # Clear hover feedback when the cursor leaves the canvas.
        self._clear_hover_vp()
        self._set_hover_conn(None)
        super().leaveEvent(event)

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
        # Right-click during a visual port move cancels it (restores position, no menu).
        if self._port_move is not None:
            self._cancel_port_move()
            return
        # Right-click during a port drag cancels it (no menu).
        if self._port_drag is not None:
            self._cancel_port_drag()
            return

        item = self.itemAt(event.pos())
        # Resolve PortDot hit to its parent PartNode
        if isinstance(item, PortDot):
            item = item.parentItem()

        scene_pos = self.mapToScene(event.pos())

        # Wire mode — normal operations stay reachable so they never "die".
        if self._mode == "wire":
            menu = QMenu(self)
            if isinstance(item, PartNode):
                if self._wire_from is None:
                    a_wire = menu.addAction("ここから接続を開始")
                else:
                    a_wire = menu.addAction("ここに接続")
                a_cancel = menu.addAction("Wire Cancel（design へ戻る）")
                menu.addSeparator()
                a_props = menu.addAction("Properties")
                a_asm   = menu.addAction("プログラムを開く")
                a_hdl   = menu.addAction("HDLを開く")
                a_clone = menu.addAction("複製")
                a_del   = menu.addAction("削除")
                chosen = menu.exec(event.globalPos())
                if chosen is None:
                    return
                if chosen is a_wire:
                    if self._wire_from is None:
                        self._begin_wire_from(item.node_id(), "bus")
                    else:
                        self._finish_wire(item.node_id(), "bus")
                elif chosen is a_cancel:
                    self._log("Wire canceled")
                    self._cancel_wire()
                elif chosen is a_props:
                    self._select_only(item)
                elif chosen is a_asm:
                    self.tab_open_requested.emit(item.part(), item.node_id(), "asm")
                elif chosen is a_hdl:
                    self.tab_open_requested.emit(item.part(), item.node_id(), "v")
                elif chosen is a_clone:
                    self._clone_node(item)
                elif chosen is a_del:
                    self._remove_node(item.node_id())
            else:
                # Blank area in wire mode
                a_wp = menu.addAction("Waypoint 追加") if self._wire_from is not None else None
                a_cancel = menu.addAction("Wire Cancel（design へ戻る）")
                chosen = menu.exec(event.globalPos())
                if chosen is None:
                    return
                if a_wp is not None and chosen is a_wp:
                    self._add_waypoint(scene_pos)
                    self._update_wire_preview(scene_pos)
                elif chosen is a_cancel:
                    self._log("Wire canceled")
                    self._cancel_wire()
            return

        # Design mode
        if not isinstance(item, PartNode):
            # Right-click near a wire: select it and offer Delete Wire.
            conn = self._connection_at(scene_pos)
            if conn is not None:
                self._set_selected_conn(conn.conn_id())
                menu = QMenu(self)
                a_del = menu.addAction("Delete Wire")
                chosen = menu.exec(event.globalPos())
                if chosen is a_del:
                    self._remove_connection(conn.conn_id())
                return
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
        menu.addAction("ポートを整列")
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
        elif label == "ポートを整列":
            self.arrange_visual_ports(item.node_id())
        elif label == "削除":
            self._remove_node(item.node_id())
        elif label == "複製":
            self._clone_node(item)
        elif label == "プログラムを開く":
            self.tab_open_requested.emit(item.part(), item.node_id(), "asm")
        elif label == "HDLを開く":
            self.tab_open_requested.emit(item.part(), item.node_id(), "v")

    def _clone_node(self, item) -> None:
        """Duplicate a single PartNode offset by 20px (shared by both menus)."""
        new_id = self._next_node_id()
        clone = PartNode(item.part(), new_id)
        clone.set_snap(self._snap_enabled)
        clone._pos_changed_cb = self.update_connections
        clone.setPos(item.pos() + QPointF(20, 20))
        self.scene().addItem(clone)
        self._log(f"Cloned: {item.part()['name']}  [{item.node_id()}] -> [{new_id}]")

    def _select_only(self, item) -> None:
        """Select just this node so the Properties panel updates."""
        self.scene().clearSelection()
        item.setSelected(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            # A selected wire takes priority over node deletion (but never during
            # an in-progress port drag, which owns its own cancel/finish flow).
            if self._selected_conn_id is not None and self._port_drag is None:
                self._remove_connection(self._selected_conn_id)
            else:
                self.delete_selected()
        elif event.key() == Qt.Key.Key_Escape and self._port_move is not None:
            # Cancel an in-progress visual port move (PATCH_VISUAL_PORT_MOVE_V05).
            self._cancel_port_move()
        elif event.key() == Qt.Key.Key_Escape and self._port_drag is not None:
            # Cancel an in-progress port drag (PATCH_PORT_DRAG_CONNECT_V05).
            self._cancel_port_drag()
        elif event.key() == Qt.Key.Key_Escape and self._mode == "wire":
            # Patch 2 (F): clear exit from wire mode.
            self._cancel_wire()
        else:
            super().keyPressEvent(event)

    def _remove_node(self, node_id: str) -> int:
        """B1: single source of truth for node removal.

        Removes the PartNode AND every connection whose endpoints reference it
        (data + ConnectionLine items), cancels any wire/pending state pointing
        at it, and refreshes the remaining wires. Returns the connection count
        removed. Used by every delete path (Delete key, menus, delete_selected).
        """
        # Cancel an in-progress wire that starts at this node.
        if self._wire_from is not None and self._wire_from.get("node_id") == node_id:
            self._cancel_wire()
        # Clear a pending port belonging to this node (legacy click flow).
        if self._pending_port is not None and self._pending_port.node_id() == node_id:
            self._pending_port.set_pending(False)
            self._pending_port = None

        # Drop connections touching this node (data + visual line items).
        kept: list[dict] = []
        removed_conns = 0
        for conn in self._connections:
            if node_id in (conn["from"]["node_id"], conn["to"]["node_id"]):
                line = self._conn_items.pop(conn["id"], None)
                if line is not None and line.scene() is not None:
                    self.scene().removeItem(line)
                removed_conns += 1
            else:
                kept.append(conn)
        self._connections = kept

        # Drop selection/hover that pointed at a now-removed connection.
        if self._selected_conn_id not in self._conn_items:
            self._selected_conn_id = None
        if self._hover_conn_id not in self._conn_items:
            self._hover_conn_id = None

        # Remove the node itself.
        node = self.get_node(node_id)
        if node is not None and node.scene() is not None:
            self.scene().removeItem(node)

        if removed_conns:
            self._log(f"  Removed {removed_conns} connection(s) attached to [{node_id}]")
        # Drop visual ports left without a connection (PATCH_WIRING_PORTS_V05).
        self._prune_orphan_visual_ports()
        self.update_connections()
        return removed_conns

    def _delete_node(self, item: "PartNode") -> None:
        """Log + remove a single PartNode through the unified delete path."""
        self._log(
            f"Removed: {item.part()['name']}  ({item.part()['id']})  [{item.node_id()}]"
        )
        self._remove_node(item.node_id())

    def delete_selected(self) -> int:
        """Remove all selected PartNodes (and their wires). Returns the count."""
        items = [i for i in self.scene().selectedItems() if isinstance(i, PartNode)]
        for item in items:
            self._delete_node(item)
        return len(items)

    def clone_selected(self) -> int:
        """Duplicate all selected PartNodes (offset by 20px). Returns count."""
        cloned = 0
        for item in list(self.scene().selectedItems()):
            if isinstance(item, PartNode):
                new_id = self._next_node_id()
                clone = PartNode(item.part(), new_id)
                clone.set_snap(self._snap_enabled)
                clone._pos_changed_cb = self.update_connections
                clone.setPos(item.pos() + QPointF(20, 20))
                self.scene().addItem(clone)
                self._log(
                    f"Cloned: {item.part()['name']}  [{item.node_id()}] -> [{new_id}]"
                )
                cloned += 1
        return cloned
