# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for ui/memview.py — MemoryViewer and hex dump helpers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from ui.memview import MemoryViewer, _hex_dump
from core.dev import RamPart


# ---------------------------------------------------------------------------
# _hex_dump unit tests
# ---------------------------------------------------------------------------

def test_hex_dump_header():
    """First line of hex dump is the column header."""
    out = _hex_dump(bytes(16))
    header = out.splitlines()[0]
    assert "Addr" in header
    assert "ASCII" in header


def test_hex_dump_first_row_address():
    """First data row starts with 0x0000."""
    out = _hex_dump(bytes(16))
    data_line = out.splitlines()[1]
    assert data_line.startswith("0x0000")


def test_hex_dump_second_row_address():
    """Second data row (bytes 16-31) shows 0x0010."""
    out = _hex_dump(bytes(32))
    data_line = out.splitlines()[2]
    assert data_line.startswith("0x0010")


def test_hex_dump_bytes_shown():
    """Known byte values appear in hex in the dump."""
    data = bytes([0x41, 0x42, 0xDE, 0xAD] + [0] * 12)
    out = _hex_dump(data)
    data_line = out.splitlines()[1]
    assert "41" in data_line
    assert "42" in data_line
    assert "DE" in data_line
    assert "AD" in data_line


def test_hex_dump_printable_ascii():
    """Printable ASCII characters appear in the ASCII column."""
    data = bytes([ord("H"), ord("i")] + [0] * 14)
    out = _hex_dump(data)
    data_line = out.splitlines()[1]
    # ASCII column is at the end; "Hi" should appear
    assert "Hi" in data_line


def test_hex_dump_non_printable_becomes_dot():
    """Non-printable bytes (< 0x20 or >= 0x7F) are shown as '.' in ASCII column."""
    data = bytes([0x00, 0x01, 0x7F, 0xFF] + [0] * 12)
    out = _hex_dump(data)
    data_line = out.splitlines()[1]
    ascii_col = data_line.split("  ")[-1]
    assert ascii_col.startswith("....")


def test_hex_dump_space_is_printable():
    """Space (0x20) is printable — should appear as ' ' not '.'."""
    data = bytes([0x20] + [0] * 15)
    out = _hex_dump(data)
    data_line = out.splitlines()[1]
    ascii_col = data_line.split("  ")[-1]
    assert ascii_col[0] == " "


def test_hex_dump_del_is_not_printable():
    """DEL (0x7F) is not printable — should appear as '.'."""
    data = bytes([0x7F] + [0] * 15)
    out = _hex_dump(data)
    data_line = out.splitlines()[1]
    ascii_col = data_line.split("  ")[-1]
    assert ascii_col[0] == "."


def test_hex_dump_empty_bytes():
    """Empty bytes produces a header and at least one row without crashing."""
    out = _hex_dump(b"")
    lines = out.splitlines()
    assert len(lines) >= 1   # at least header
    assert "Addr" in lines[0]


def test_hex_dump_partial_row():
    """A partial last row (< 16 bytes) is handled correctly."""
    data = bytes([0xAB, 0xCD])
    out = _hex_dump(data)
    lines = out.splitlines()
    assert len(lines) == 2   # header + 1 data line
    assert "AB" in lines[1]
    assert "CD" in lines[1]


def test_hex_dump_256_bytes_rows():
    """256 bytes → 16 data rows + 1 header = 17 lines total."""
    out = _hex_dump(bytes(256))
    assert len(out.splitlines()) == 17


# ---------------------------------------------------------------------------
# MemoryViewer widget tests
# ---------------------------------------------------------------------------

def test_memory_viewer_creates():
    """MemoryViewer can be instantiated without error."""
    mv = MemoryViewer()
    assert mv is not None


def test_memory_viewer_update_from_ram():
    """update_from_ram() with a valid RamPart populates the text widget."""
    mv = MemoryViewer()
    ram = RamPart("r", "RAM", size=64, base=0)
    mv.update_from_ram(ram)
    text = mv._text.toPlainText()
    assert "0x0000" in text
    assert "Addr" in text


def test_memory_viewer_update_none_no_crash():
    """update_from_ram(None) does not crash."""
    mv = MemoryViewer()
    mv.update_from_ram(None)   # must not raise


def test_memory_viewer_update_empty_ram():
    """update_from_ram() on a 16-byte RAM shows at least header + 1 row."""
    mv = MemoryViewer()
    ram = RamPart("r", "RAM", size=16, base=0)
    mv.update_from_ram(ram)
    lines = mv._text.toPlainText().splitlines()
    assert len(lines) >= 2


def test_memory_viewer_reflects_ram_content():
    """After load_bytes(), update_from_ram() shows the loaded bytes."""
    mv = MemoryViewer()
    ram = RamPart("r", "RAM", size=16, base=0)
    ram.load_bytes(bytes([0xCA, 0xFE, 0xBA, 0xBE, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    mv.update_from_ram(ram)
    text = mv._text.toPlainText()
    assert "CA" in text
    assert "FE" in text
    assert "BA" in text
    assert "BE" in text


def test_memory_viewer_highlight_addr_no_crash():
    """highlight_addr() does not crash even if PC is out of current data range."""
    mv = MemoryViewer()
    ram = RamPart("r", "RAM", size=32, base=0)
    mv.update_from_ram(ram)
    mv.highlight_addr(0x0000)   # first row
    mv.highlight_addr(0x0010)   # second row
    mv.highlight_addr(0xFFFF)   # way out of range


def test_memory_viewer_highlight_addr_before_update_no_crash():
    """highlight_addr() called before update_from_ram() does not crash."""
    mv = MemoryViewer()
    mv.highlight_addr(0)


def test_memory_viewer_update_twice_no_crash():
    """Calling update_from_ram() twice refreshes the display without error."""
    mv = MemoryViewer()
    ram = RamPart("r", "RAM", size=16, base=0)
    mv.update_from_ram(ram)
    ram.load_bytes(bytes([0xFF] * 16))
    mv.update_from_ram(ram)
    text = mv._text.toPlainText()
    assert "FF" in text


def test_memory_viewer_dock_title():
    """MemoryViewer dock widget has the title 'Memory'."""
    mv = MemoryViewer()
    assert mv.windowTitle() == "Memory"


# ---------------------------------------------------------------------------
# Integration: MainWin uses MemoryViewer
# ---------------------------------------------------------------------------

def test_mainwin_has_mem_viewer():
    """MainWin creates a _mem_viewer attribute."""
    from ui.win import MainWin
    win = MainWin()
    assert hasattr(win, "_mem_viewer")
    assert isinstance(win._mem_viewer, MemoryViewer)


def test_mainwin_update_memory_viewer_no_crash():
    """_update_memory_viewer() does not crash on a fresh MainWin."""
    from ui.win import MainWin
    win = MainWin()
    win._update_memory_viewer()
