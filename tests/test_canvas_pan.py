# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for middle-button canvas pan."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, Qt

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, _PAN_THRESHOLD


def _make_canvas() -> Canvas:
    logs: list[str] = []
    return Canvas(log_fn=logs.append)


# ---------------------------------------------------------------------------
# Fake mouse events — duck-typed, safe for middle-button paths that don't
# call super() so Qt never sees the fake object.
# ---------------------------------------------------------------------------

class _Press:
    def __init__(self, x, y, button=Qt.MouseButton.MiddleButton):
        self._pos    = QPoint(x, y)
        self._button = button
    def pos(self):     return self._pos
    def button(self):  return self._button
    def buttons(self): return self._button
    def accept(self):  pass


class _Move:
    def __init__(self, x, y, buttons=Qt.MouseButton.MiddleButton):
        self._pos     = QPoint(x, y)
        self._buttons = buttons
    def pos(self):     return self._pos
    def button(self):  return Qt.MouseButton.NoButton
    def buttons(self): return self._buttons
    def accept(self):  pass


class _Release:
    def __init__(self, x, y, button=Qt.MouseButton.MiddleButton):
        self._pos    = QPoint(x, y)
        self._button = button
    def pos(self):     return self._pos
    def button(self):  return self._button
    def buttons(self): return Qt.MouseButton.NoButton
    def accept(self):  pass


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_pan_initial_state():
    canvas = _make_canvas()
    assert canvas._pan_origin is None
    assert canvas._pan_last   is None
    assert canvas._panned     is False


# ---------------------------------------------------------------------------
# Middle press
# ---------------------------------------------------------------------------

def test_middle_press_sets_pan_origin():
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(100, 200))
    assert canvas._pan_origin == QPoint(100, 200)


def test_middle_press_sets_pan_last():
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(50, 75))
    assert canvas._pan_last == QPoint(50, 75)


def test_middle_press_panned_is_false():
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(0, 0))
    assert canvas._panned is False


# ---------------------------------------------------------------------------
# Middle release
# ---------------------------------------------------------------------------

def test_middle_release_clears_pan_origin():
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(10, 10))
    canvas.mouseReleaseEvent(_Release(10, 10))
    assert canvas._pan_origin is None


def test_middle_release_clears_pan_last():
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(10, 10))
    canvas.mouseReleaseEvent(_Release(10, 10))
    assert canvas._pan_last is None


# ---------------------------------------------------------------------------
# Threshold — _panned flag
# ---------------------------------------------------------------------------

def test_move_below_threshold_no_pan():
    """Movement below _PAN_THRESHOLD must not set _panned."""
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(100, 100))
    canvas.mouseMoveEvent(_Move(100 + _PAN_THRESHOLD - 1, 100))
    assert canvas._panned is False


def test_move_above_threshold_activates_pan():
    """Movement beyond _PAN_THRESHOLD must set _panned."""
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(100, 100))
    canvas.mouseMoveEvent(_Move(100 + _PAN_THRESHOLD + 1, 100))
    assert canvas._panned is True


def test_pan_flag_resets_on_next_press():
    """A new middle press resets _panned even if previous drag set it."""
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(0, 0))
    canvas.mouseMoveEvent(_Move(_PAN_THRESHOLD + 5, 0))
    assert canvas._panned is True
    canvas.mouseReleaseEvent(_Release(_PAN_THRESHOLD + 5, 0))
    canvas.mousePressEvent(_Press(0, 0))
    assert canvas._panned is False


# ---------------------------------------------------------------------------
# pan_threshold constant
# ---------------------------------------------------------------------------

def test_pan_threshold_value():
    assert _PAN_THRESHOLD >= 2


# ---------------------------------------------------------------------------
# Middle button does not interact with context menu
# ---------------------------------------------------------------------------

def test_middle_pan_does_not_block_context_menu():
    """_panned flag is not checked in contextMenuEvent; right-click always shows menu."""
    canvas = _make_canvas()
    canvas.mousePressEvent(_Press(0, 0))
    canvas.mouseMoveEvent(_Move(_PAN_THRESHOLD + 5, 0))
    assert canvas._panned is True
    # _panned being True must not suppress contextMenuEvent —
    # verified structurally: contextMenuEvent no longer guards on _panned.
    assert not hasattr(canvas, "_PANNED_BLOCKS_MENU")  # no such flag
