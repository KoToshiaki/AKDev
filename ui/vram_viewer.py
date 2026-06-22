# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""VRAM Viewer panel — minimal framebuffer display (PATCH_GAME_RUNTIME_MINIMAL_V08).

A small dock that renders a :class:`core.dev.VramPart` framebuffer (indexed color,
1 byte per pixel) as a grayscale image scaled up for visibility:

  * 0   -> black
  * 255 -> white
  * any value in between -> the matching gray level

It only *reads* the VRAM (``dump()`` / ``width`` / ``height``); it never mutates the
device. No palette, sprites or tiles — just the raw framebuffer. When no VRAM device
is placed the panel shows ``VRAM: None``. ``snapshot()`` / ``pixel()`` expose the last
rendered bytes for tests (so the viewer can be checked headless without GUI capture).
"""
from __future__ import annotations

from PySide6.QtGui import QImage, QPixmap, qRgb
from PySide6.QtWidgets import QDockWidget, QLabel, QWidget
from PySide6.QtCore import Qt

_DEFAULT_SCALE = 6   # each VRAM pixel drawn as a 6x6 block


class VramViewer(QDockWidget):
    """Dock panel that shows a grayscale image of a VRAM framebuffer."""

    def __init__(self, parent: QWidget | None = None, scale: int = _DEFAULT_SCALE):
        super().__init__("VRAM Viewer", parent)
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
                             | Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._scale = max(1, int(scale))
        self._label = QLabel("VRAM: None")
        self._label.setAlignment(Qt.AlignCenter)
        self.setWidget(self._label)

        # Last rendered framebuffer (for refresh checks / tests).
        self._data: bytes = b""
        self._width = 0
        self._height = 0

    # ------------------------------------------------------------------ public

    def update_from_vram(self, vram_part) -> None:
        """Refresh the display from a VramPart (or any object with ``dump()``).

        ``None`` (no VRAM placed) clears the panel to ``VRAM: None`` — harmless for
        existing projects. Read errors are shown without raising.
        """
        if vram_part is None:
            self._data = b""
            self._width = self._height = 0
            self._label.setPixmap(QPixmap())   # clear any previous image
            self._label.setText("VRAM: None")
            return
        try:
            data = bytes(vram_part.dump())
            width = int(getattr(vram_part, "width", 32))
            height = int(getattr(vram_part, "height", 32))
        except Exception:
            self._data = b""
            self._width = self._height = 0
            self._label.setPixmap(QPixmap())
            self._label.setText("VRAM: (read error)")
            return

        self._data = data
        self._width = width
        self._height = height
        self._label.setPixmap(self._render(data, width, height))

    def snapshot(self) -> bytes:
        """Return the last rendered framebuffer bytes (empty when no VRAM)."""
        return self._data

    def pixel(self, x: int, y: int) -> int:
        """Return the last rendered 1-byte pixel at (x, y); out of range -> 0."""
        if self._width <= 0:
            return 0
        idx = y * self._width + x
        if 0 <= idx < len(self._data):
            return self._data[idx]
        return 0

    def is_active(self) -> bool:
        """True when a VRAM framebuffer is currently displayed."""
        return bool(self._data)

    # ------------------------------------------------------------------ helpers

    def _render(self, data: bytes, width: int, height: int) -> QPixmap:
        """Build a scaled grayscale QPixmap from 1-byte-per-pixel data."""
        img = QImage(width, height, QImage.Format_RGB32)
        for y in range(height):
            row = y * width
            for x in range(width):
                idx = row + x
                v = data[idx] if idx < len(data) else 0
                img.setPixel(x, y, qRgb(v, v, v))
        pix = QPixmap.fromImage(img)
        return pix.scaled(width * self._scale, height * self._scale,
                          Qt.IgnoreAspectRatio, Qt.FastTransformation)
