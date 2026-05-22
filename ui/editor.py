# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""EditorTabs — closable part-editor tab widget with dirty-state tracking."""
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTabWidget, QTextEdit

from ui.highlighter import attach_highlighter, attach_line_highlight


class _TabInfo:
    """Metadata for one open editor tab."""

    def __init__(self, node_id: str, part_id: str, ext: str,
                 base_name: str, save_path: Path):
        self.node_id   = node_id
        self.part_id   = part_id
        self.ext       = ext
        self.base_name = base_name   # display name without *
        self.save_path = save_path
        self.dirty     = False


class EditorTabs(QTabWidget):
    """Central tab editor. One tab per (node_id, ext) pair; no duplicates."""

    _SAVE_DIR = Path("build/edit")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self._close_tab)
        self._open: dict[tuple[str, str], QTextEdit] = {}  # (node_id, ext) -> widget
        self._meta: dict[QTextEdit, _TabInfo]        = {}  # widget -> metadata

    # ------------------------------------------------------------------ public

    def open_tab(self, part: dict, node_id: str, ext: str) -> str | None:
        """Open (or focus) a tab for the given node + extension.

        Returns the tab name if a new tab was created, None if already open.
        """
        key = (node_id, ext)
        if key in self._open:
            self.setCurrentWidget(self._open[key])
            return None

        base_name = f"{part['name']} [{node_id}].{ext}"
        info = _TabInfo(
            node_id   = node_id,
            part_id   = part["id"],
            ext       = ext,
            base_name = base_name,
            save_path = self._SAVE_DIR / f"{node_id}.{ext}",
        )
        editor = QTextEdit()
        editor.setPlaceholderText(f"# {base_name}\n")
        editor.setFont(QFont("Courier New", 10))
        attach_highlighter(editor, ext)
        attach_line_highlight(editor)
        self.addTab(editor, base_name)
        self._open[key] = editor
        self._meta[editor] = info
        # Load saved content before connecting signal so dirty flag stays clear.
        if info.save_path.exists():
            editor.setPlainText(info.save_path.read_text(encoding="utf-8"))
        # connect after addTab so spurious init signals don't trigger dirty
        editor.textChanged.connect(lambda: self._mark_dirty(editor))
        self.setCurrentWidget(editor)
        return base_name

    def save_current(self) -> str | None:
        """Save the active tab's content to build/edit/<node_id>.<ext>.

        Returns the POSIX path string on success, None if nothing to save.
        """
        editor = self.currentWidget()
        if not isinstance(editor, QTextEdit):
            return None
        info = self._meta.get(editor)
        if info is None:
            return None

        info.save_path.parent.mkdir(parents=True, exist_ok=True)
        info.save_path.write_text(editor.toPlainText(), encoding="utf-8")
        info.dirty = False
        self.setTabText(self.indexOf(editor), info.base_name)
        return info.save_path.as_posix()

    # ------------------------------------------------------------------ private

    def _mark_dirty(self, editor: QTextEdit):
        info = self._meta.get(editor)
        if info is None or info.dirty:
            return
        info.dirty = True
        self.setTabText(self.indexOf(editor), f"{info.base_name}*")

    def _close_tab(self, index: int):
        widget = self.widget(index)
        key_to_remove = next(
            (k for k, w in self._open.items() if w is widget), None
        )
        if key_to_remove:
            del self._open[key_to_remove]
        if isinstance(widget, QTextEdit) and widget in self._meta:
            del self._meta[widget]
        self.removeTab(index)
