# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Syntax highlighters and current-line highlight for the editor tabs."""
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor, QFont, QSyntaxHighlighter, QTextCharFormat,
)
from PySide6.QtWidgets import QTextEdit

# QTextFormat::FullWidthSelection integer constant (Qt6 value = 32784)
_FULL_WIDTH_SELECTION = 32784

_LINE_BG = QColor("#fffacd")   # lemon chiffon — readable on default white bg


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    if italic:
        f.setFontItalic(True)
    return f


class AsmHighlighter(QSyntaxHighlighter):
    """Minimal syntax highlighter for AK32 assembly."""

    _KEYWORDS = (
        "NOP", "HALT", "LDI", "LD", "ST",
        "ADD", "SUB", "AND", "OR", "XOR", "SHL", "SHR",
        "JMP", "BEQ", "BNE", "CALL", "RET", "IN", "OUT",
    )

    def __init__(self, doc):
        super().__init__(doc)
        CI = QRegularExpression.PatternOption.CaseInsensitiveOption
        self._rules = [
            # instructions — word boundary, case-insensitive
            (QRegularExpression(r"\b(" + "|".join(self._KEYWORDS) + r")\b", CI),
             _fmt("#0000cc", bold=True)),
            # registers r0-r15
            (QRegularExpression(r"\br1[0-5]\b|\br[0-9]\b", CI),
             _fmt("#007070")),
            # hex literals 0x...
            (QRegularExpression(r"\b0x[0-9a-fA-F]+\b", CI),
             _fmt("#8b4513")),
            # comments: # to end of line (applied last — wins over above)
            (QRegularExpression(r"#[^\n]*"),
             _fmt("#808080", italic=True)),
        ]

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class VerilogHighlighter(QSyntaxHighlighter):
    """Minimal syntax highlighter for Verilog / SystemVerilog."""

    _KEYWORDS = (
        "module", "endmodule", "input", "output", "inout",
        "wire", "reg", "logic", "always", "assign",
        "begin", "end", "if", "else", "case", "endcase",
        "posedge", "negedge", "initial", "parameter",
    )

    def __init__(self, doc):
        super().__init__(doc)
        self._rules = [
            # keywords
            (QRegularExpression(r"\b(" + "|".join(self._KEYWORDS) + r")\b"),
             _fmt("#800080", bold=True)),
            # Verilog numeric literals: 8'b0101, 16'hFF, plain integers
            (QRegularExpression(r"\b\d+('[bBoOhHdD][0-9a-fA-F_x]+)?\b"),
             _fmt("#8b4513")),
            # single-line comments: // to end of line (applied last)
            (QRegularExpression(r"//[^\n]*"),
             _fmt("#808080", italic=True)),
        ]

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


_HIGHLIGHTERS: dict[str, type] = {
    "asm": AsmHighlighter,
    "v":   VerilogHighlighter,
}


def attach_highlighter(editor: QTextEdit, ext: str) -> None:
    """Attach the appropriate syntax highlighter to the editor's document."""
    cls = _HIGHLIGHTERS.get(ext)
    if cls:
        cls(editor.document())   # document takes ownership — GC-safe


def attach_line_highlight(editor: QTextEdit) -> None:
    """Highlight the current cursor line with a subtle background."""
    def _update():
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(_LINE_BG)
        sel.format.setProperty(_FULL_WIDTH_SELECTION, True)
        sel.cursor = editor.textCursor()
        sel.cursor.clearSelection()
        editor.setExtraSelections([sel])

    editor.cursorPositionChanged.connect(_update)
    _update()
