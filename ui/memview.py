# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Memory Viewer panel — hex dump of simulator RAM."""
from __future__ import annotations

from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QDockWidget, QPlainTextEdit, QWidget
from PySide6.QtCore import Qt

_BYTES_PER_ROW = 16
_HIGHLIGHT_COLOR = QColor(0xFF, 0xFF, 0xCC)   # pale yellow


def _hex_dump(data: bytes) -> str:
    """Return a hex dump string for *data* (16 bytes per row)."""
    lines: list[str] = [
        "Addr     "
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII"
    ]
    n = len(data)
    for row_start in range(0, max(n, 1), _BYTES_PER_ROW):
        chunk = data[row_start: row_start + _BYTES_PER_ROW]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        # pad to full row width if chunk is short
        hex_part = hex_part.ljust(_BYTES_PER_ROW * 3 - 1)
        ascii_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
        lines.append(f"0x{row_start:04X}   {hex_part}  {ascii_part}")
    return "\n".join(lines)


class MemoryViewer(QDockWidget):
    """Dock panel that shows a hex dump of a RamPart."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Memory", parent)
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setPlaceholderText("Memory not loaded...")
        font = self._text.font()
        font.setFamily("Courier New")
        font.setPointSize(9)
        self._text.setFont(font)
        self.setWidget(self._text)

        self._row_count = 0   # number of data rows (excluding header)

    # ------------------------------------------------------------------ public

    def update_from_ram(self, ram_part) -> None:
        """Refresh display from a RamPart (or any object with .dump())."""
        if ram_part is None:
            self._text.setPlainText("")
            self._row_count = 0
            return
        try:
            data = ram_part.dump()
        except Exception:
            self._text.setPlainText("(read error)")
            self._row_count = 0
            return
        dump = _hex_dump(data)
        self._text.setPlainText(dump)
        self._row_count = (len(data) + _BYTES_PER_ROW - 1) // _BYTES_PER_ROW

    def highlight_addr(self, pc: int) -> None:
        """Highlight the row that contains address *pc* with pale yellow."""
        row_index = pc // _BYTES_PER_ROW   # 0-based data row
        # line 0 is the header; data rows start at line 1
        target_line = row_index + 1

        doc = self._text.document()
        if target_line >= doc.blockCount():
            return

        fmt = QTextCharFormat()
        fmt.setBackground(_HIGHLIGHT_COLOR)

        # Clear existing background on all lines first
        clear_fmt = QTextCharFormat()
        clear_fmt.setBackground(QColor(Qt.GlobalColor.transparent))

        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(clear_fmt)

        # Highlight target line
        block = doc.findBlockByLineNumber(target_line)
        if not block.isValid():
            return
        line_cursor = QTextCursor(block)
        line_cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_cursor.setCharFormat(fmt)
