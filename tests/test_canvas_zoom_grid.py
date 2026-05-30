# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests for Canvas UX Patch 1B: Zoom / Grid."""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

_app = QApplication.instance() or QApplication(sys.argv)

from ui.canvas import Canvas, GridScene, PartNode

_PART_A = {"id": "cpu.ak32", "name": "AK32", "category": "cpu"}


def _make_canvas() -> Canvas:
    logs: list[str] = []
    return Canvas(log_fn=logs.append)


# ---------------------------------------------------------------------------
# Zoom — basic behaviour
# ---------------------------------------------------------------------------

def test_zoom_in_increases_scale():
    canvas = _make_canvas()
    canvas.zoom_in()
    assert canvas.transform().m11() > 1.0


def test_zoom_out_decreases_scale():
    canvas = _make_canvas()
    canvas.zoom_out()
    assert canvas.transform().m11() < 1.0


def test_reset_zoom_restores_identity():
    canvas = _make_canvas()
    canvas.zoom_in()
    canvas.zoom_in()
    canvas.reset_zoom()
    assert canvas.transform().m11() == pytest.approx(1.0)


def test_zoom_in_then_out_roughly_identity():
    """zoom_in followed by zoom_out returns close to 1.0 (1.25 * 0.8 = 1.0)."""
    canvas = _make_canvas()
    canvas.zoom_in()
    canvas.zoom_out()
    assert canvas.transform().m11() == pytest.approx(1.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Zoom — limits
# ---------------------------------------------------------------------------

def test_zoom_in_capped_at_maximum():
    """Repeated zoom_in does not exceed _ZOOM_MAX."""
    canvas = _make_canvas()
    for _ in range(200):
        canvas.zoom_in()
    assert canvas.transform().m11() <= 10.0 + 0.5


def test_zoom_out_capped_at_minimum():
    """Repeated zoom_out does not fall below _ZOOM_MIN."""
    canvas = _make_canvas()
    for _ in range(200):
        canvas.zoom_out()
    assert canvas.transform().m11() >= 0.1 - 0.05


# ---------------------------------------------------------------------------
# fit_to_view — crash safety
# ---------------------------------------------------------------------------

def test_fit_to_view_empty_scene_no_crash():
    canvas = _make_canvas()
    canvas.fit_to_view()   # must not raise


def test_fit_to_view_with_items_no_crash():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0, 0.0))
    canvas.fit_to_view()   # must not raise


def test_fit_to_view_multiple_items_no_crash():
    canvas = _make_canvas()
    canvas.add_part_at(_PART_A, QPointF(0.0,   0.0))
    canvas.add_part_at(_PART_A, QPointF(200.0, 150.0))
    canvas.fit_to_view()   # must not raise


# ---------------------------------------------------------------------------
# GridScene — type and defaults
# ---------------------------------------------------------------------------

def test_canvas_uses_grid_scene():
    canvas = _make_canvas()
    assert isinstance(canvas.scene(), GridScene)


def test_grid_size_constant():
    assert GridScene.GRID_SIZE == 20


def test_grid_visible_default_true():
    canvas = _make_canvas()
    assert canvas.scene().grid_visible() is True


# ---------------------------------------------------------------------------
# GridScene — toggle
# ---------------------------------------------------------------------------

def test_set_grid_visible_false():
    canvas = _make_canvas()
    canvas.set_grid_visible(False)
    assert canvas.scene().grid_visible() is False


def test_set_grid_visible_true():
    canvas = _make_canvas()
    canvas.set_grid_visible(False)
    canvas.set_grid_visible(True)
    assert canvas.scene().grid_visible() is True


def test_grid_scene_set_directly():
    scene = GridScene()
    assert scene.grid_visible() is True
    scene.set_grid_visible(False)
    assert scene.grid_visible() is False


# ---------------------------------------------------------------------------
# Wheel zoom — transformation anchor and event dispatch
# ---------------------------------------------------------------------------

class _FakeWheelEvent:
    """Minimal duck-type stand-in for QWheelEvent used in direct wheelEvent calls."""

    def __init__(self, delta_y: int):
        self._delta_y = delta_y
        self.accepted = False

    def angleDelta(self):
        class _Delta:
            def __init__(self, y): self._y = y
            def y(self): return self._y
        return _Delta(self._delta_y)

    def accept(self):
        self.accepted = True


def test_transformation_anchor_is_under_mouse():
    from PySide6.QtWidgets import QGraphicsView
    canvas = _make_canvas()
    assert canvas.transformationAnchor() == QGraphicsView.ViewportAnchor.AnchorUnderMouse


def test_wheel_forward_zooms_in():
    canvas = _make_canvas()
    event = _FakeWheelEvent(120)
    canvas.wheelEvent(event)
    assert canvas.transform().m11() > 1.0
    assert event.accepted is True


def test_wheel_backward_zooms_out():
    canvas = _make_canvas()
    event = _FakeWheelEvent(-120)
    canvas.wheelEvent(event)
    assert canvas.transform().m11() < 1.0
    assert event.accepted is True


def test_wheel_zoom_in_uses_existing_limit():
    """Repeated wheel-forward hits the same upper bound as zoom_in()."""
    canvas = _make_canvas()
    for _ in range(200):
        canvas.wheelEvent(_FakeWheelEvent(120))
    assert canvas.transform().m11() <= 10.0 + 0.5


def test_wheel_zoom_out_uses_existing_limit():
    """Repeated wheel-backward hits the same lower bound as zoom_out()."""
    canvas = _make_canvas()
    for _ in range(200):
        canvas.wheelEvent(_FakeWheelEvent(-120))
    assert canvas.transform().m11() >= 0.1 - 0.05
