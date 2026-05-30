# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""EditorTabs — closable part-editor tab widget with dirty-state tracking."""
from pathlib import Path
from typing import NamedTuple

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTabWidget, QTextEdit

from ui.highlighter import attach_highlighter, attach_line_highlight

_FORBIDDEN_CHARS = frozenset('\\/:*?"<>|')


def validate_source_name(name: str, ext: str) -> "str | None":
    """Return an error message if name is invalid for use as src/<name>, else None.

    ext is the bare extension without dot, e.g. "asm" or "v".
    """
    stripped = name.strip()
    if not stripped:
        return "ファイル名が空です"
    p = Path(stripped)
    if p.is_absolute():
        return "絶対パスは使用できません"
    if ".." in p.parts:
        return "'..' を含むパスは使用できません"
    allowed = f".{ext}"
    if p.suffix.lower() != allowed:
        return f"拡張子は {allowed} のみ使用できます"
    if not p.stem:
        return "ファイル名（拡張子なし部分）が空です"
    if any(c in _FORBIDDEN_CHARS for c in stripped):
        return "使用できない文字が含まれています"
    return None


class CurrentTabInfo(NamedTuple):
    """Snapshot of the currently active editor tab."""
    node_id: str
    ext: str
    text: str
    source_name: str   # user-facing filename, e.g. "main.asm"


class _TabInfo:
    """Metadata for one open editor tab."""

    def __init__(self, node_id: str, part_id: str, ext: str,
                 source_name: str, save_path: Path):
        self.node_id     = node_id
        self.part_id     = part_id
        self.ext         = ext
        self.source_name = source_name
        self.save_path   = save_path
        self.dirty       = False
        self.set_pc_line = None   # callable injected after editor creation


class EditorTabs(QTabWidget):
    """Central tab editor. One tab per (node_id, ext) pair; no duplicates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self._close_tab)
        self._open: dict[tuple[str, str], QTextEdit] = {}   # (node_id, ext) -> widget
        self._meta: dict[QTextEdit, _TabInfo]        = {}   # widget -> metadata
        self._project_root: Path | None = None

    # ------------------------------------------------------------------ public

    def set_project_root(self, root: "Path | None") -> None:
        """Set the project root for file I/O.  None means no project is open."""
        self._project_root = root

    def open_tab(self, part: dict, node_id: str, ext: str,
                 source_name: str) -> "str | None":
        """Open (or focus) a tab for the given node + extension.

        source_name: user-facing filename like "main.asm".
        Returns source_name if a new tab was opened, None if already open or
        if project_root is not set.
        """
        if self._project_root is None:
            return None

        key = (node_id, ext)
        if key in self._open:
            self.setCurrentWidget(self._open[key])
            return None

        save_path = self._project_root / "src" / source_name
        info = _TabInfo(
            node_id     = node_id,
            part_id     = part["id"],
            ext         = ext,
            source_name = source_name,
            save_path   = save_path,
        )
        editor = QTextEdit()
        editor.setPlaceholderText(f"# {source_name}\n")
        editor.setFont(QFont("Courier New", 10))
        attach_highlighter(editor, ext)
        info.set_pc_line = attach_line_highlight(editor)
        self.addTab(editor, source_name)
        self._open[key] = editor
        self._meta[editor] = info
        # Load saved content before connecting signal so dirty flag stays clear.
        if info.save_path.exists():
            editor.setPlainText(info.save_path.read_text(encoding="utf-8"))
        editor.textChanged.connect(lambda: self._mark_dirty(editor))
        self.setCurrentWidget(editor)
        return source_name

    def current_tab_info(self) -> "CurrentTabInfo | None":
        """Return node_id, ext, text and source_name of the active tab, or None."""
        editor = self.currentWidget()
        if not isinstance(editor, QTextEdit):
            return None
        info = self._meta.get(editor)
        if info is None:
            return None
        return CurrentTabInfo(info.node_id, info.ext,
                              editor.toPlainText(), info.source_name)

    def highlight_line(self, line_no: int) -> None:
        """Highlight the given 0-origin line as the current PC position."""
        editor = self.currentWidget()
        if not isinstance(editor, QTextEdit):
            return
        info = self._meta.get(editor)
        if info is None or info.set_pc_line is None:
            return
        info.set_pc_line(line_no)

    def clear_highlight(self) -> None:
        """Clear the PC line highlight in the active editor tab."""
        editor = self.currentWidget()
        if not isinstance(editor, QTextEdit):
            return
        info = self._meta.get(editor)
        if info is None or info.set_pc_line is None:
            return
        info.set_pc_line(None)

    def save_current(self) -> "str | None":
        """Save the active tab to project_root/src/<source_name>.

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
        self.setTabText(self.indexOf(editor), info.source_name)
        return info.save_path.as_posix()

    def close_all_tabs(self) -> None:
        """Close all open editor tabs (used when switching projects)."""
        while self.count() > 0:
            self._close_tab(0)

    # ------------------------------------------------------------------ private

    def _mark_dirty(self, editor: QTextEdit):
        info = self._meta.get(editor)
        if info is None or info.dirty:
            return
        info.dirty = True
        self.setTabText(self.indexOf(editor), f"{info.source_name}*")

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
