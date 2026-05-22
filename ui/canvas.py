# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""System Canvas — QGraphicsView with draggable PartNode items."""
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QColor, QBrush, QPen, QFont
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView, QMenu


_NODE_W = 140
_NODE_H = 56
_GAP_X  = 20
_GAP_Y  = 14
_COLS   = 5
_ORIGIN = QPointF(40, 40)

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


class PartNode(QGraphicsItem):
    """A single draggable/selectable part rectangle on the canvas."""

    def __init__(self, part: dict):
        super().__init__()
        self._part = part
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

    def part(self) -> dict:
        return self._part

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

    selection_changed  = Signal(list)         # list[PartNode]
    tab_open_requested = Signal(dict, str)    # (part, ext)

    def __init__(self, log_fn=None):
        super().__init__()
        self.setScene(QGraphicsScene(self))   # parent=self prevents GC
        self._log       = log_fn or (lambda s: None)
        self._place_col = 0
        self._place_row = 0
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.scene().selectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------ private

    def _on_selection_changed(self):
        items = [i for i in self.scene().selectedItems() if isinstance(i, PartNode)]
        self.selection_changed.emit(items)

    # ------------------------------------------------------------------ public

    def add_part(self, part: dict):
        node = PartNode(part)
        x = _ORIGIN.x() + self._place_col * (_NODE_W + _GAP_X)
        y = _ORIGIN.y() + self._place_row * (_NODE_H + _GAP_Y)
        node.setPos(QPointF(x, y))
        self.scene().addItem(node)
        self._log(f"Added: {part['name']}  ({part['id']})")
        self._place_col += 1
        if self._place_col >= _COLS:
            self._place_col = 0
            self._place_row += 1

    # ------------------------------------------------------------------ events

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if not isinstance(item, PartNode):
            super().contextMenuEvent(event)
            return

        name = item.part()["name"]
        menu  = QMenu(self)
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

        if label == "削除":
            self.scene().removeItem(item)
        elif label == "複製":
            clone = PartNode(item.part())
            clone.setPos(item.pos() + QPointF(20, 20))
            self.scene().addItem(clone)
        elif label == "プログラムを開く":
            self.tab_open_requested.emit(item.part(), "asm")
        elif label == "HDLを開く":
            self.tab_open_requested.emit(item.part(), "v")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene().selectedItems():
                if isinstance(item, PartNode):
                    self._log(f"Removed: {item.part()['name']}  ({item.part()['id']})")
                    self.scene().removeItem(item)
        else:
            super().keyPressEvent(event)
