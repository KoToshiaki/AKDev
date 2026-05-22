# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless test for EditorTabs: saved content is restored on re-open (B-1)."""
import sys
import tempfile
from pathlib import Path

# Ensure project root is on the import path when run directly from tests/.
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

# Bootstrap a QApplication before importing any Qt widget class.
_app = QApplication.instance() or QApplication(sys.argv)

from ui.editor import EditorTabs  # noqa: E402


_FAKE_PART = {"id": "ak32_cpu", "name": "AK32 CPU"}


def test_content_restored_after_close_and_reopen(tmp_path):
    """Open tab → write → save → close → reopen: content must be restored."""
    # Redirect save directory to a temp path so tests don't pollute build/.
    EditorTabs._SAVE_DIR = tmp_path

    tabs = EditorTabs()
    node_id = "node_0001"
    ext = "asm"

    # 1. Open a new tab.
    tabs.open_tab(_FAKE_PART, node_id, ext)

    # 2. Write content into the editor.
    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText("; hello world\nLDI r1, 72\nHALT")

    # 3. Save to disk.
    saved_path = tabs.save_current()
    assert saved_path is not None
    assert Path(saved_path).exists()

    # 4. Close the tab.
    tabs._close_tab(tabs.currentIndex())
    assert (node_id, ext) not in tabs._open

    # 5. Reopen the same tab.
    tabs.open_tab(_FAKE_PART, node_id, ext)
    editor2 = tabs.currentWidget()
    assert isinstance(editor2, QTextEdit)

    # 6. Content must be restored and dirty flag must NOT be set.
    assert editor2.toPlainText() == "; hello world\nLDI r1, 72\nHALT"
    meta = tabs._meta[editor2]
    assert not meta.dirty, "Tab should not be marked dirty after reload"

    print("PASS: content restored, dirty=False")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        test_content_restored_after_close_and_reopen(Path(d))
