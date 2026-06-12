# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Visual identity for AKDev — accent color and application stylesheet.

This is the single place where the v0.5 prototype look-and-feel lives.
``STYLESHEET`` is applied app-wide in ``main.py``; individual widgets stay
free of inline styling so the theme can be swapped later.

No external icon library or downloaded asset is used — only colors and QSS.
"""

# --- Accent / palette ------------------------------------------------------
ACCENT       = "#3B82F6"   # primary accent (blue)
ACCENT_HOVER = "#2563EB"   # hover / pressed accent
ACCENT_LIGHT = "#DBEAFE"   # selected background tint
ACCENT_TEXT  = "#FFFFFF"   # text on accent

BG       = "#F4F5F7"       # window background
SURFACE  = "#FFFFFF"       # panel / card surface
BORDER   = "#D8DCE3"       # soft border (weakened, not harsh)
TEXT     = "#1F2430"       # primary text
TEXT_DIM = "#5B6472"       # secondary text

# Application name shown in Hub and window titles.
APP_NAME    = "AKDev"
APP_TAGLINE = "Custom CPU / FPGA / Game Console Development Environment"


# --- App-wide stylesheet ---------------------------------------------------
# Buttons get soft borders + clear hover/selected/active states so the UI
# feels less "もっさり" without changing fonts.
STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {BG};
    color: {TEXT};
}}

/* Ribbon / toolbar buttons ------------------------------------------------ */
QToolButton {{
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 10px;
    background: transparent;
}}
QToolButton:hover {{
    background: {ACCENT_LIGHT};
    border: 1px solid {BORDER};
}}
QToolButton:pressed {{
    background: {ACCENT};
    color: {ACCENT_TEXT};
}}
QToolButton:checked {{
    background: {ACCENT_LIGHT};
    border: 1px solid {ACCENT};
    color: {ACCENT_HOVER};
}}
QToolButton:disabled {{
    color: {TEXT_DIM};
}}

/* Push buttons (Hub) ------------------------------------------------------ */
QPushButton {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    background: {SURFACE};
}}
QPushButton:hover {{
    border: 1px solid {ACCENT};
    background: {ACCENT_LIGHT};
}}
QPushButton:pressed {{
    background: {ACCENT};
    color: {ACCENT_TEXT};
}}
QPushButton#PrimaryButton {{
    background: {ACCENT};
    color: {ACCENT_TEXT};
    border: 1px solid {ACCENT};
}}
QPushButton#PrimaryButton:hover {{
    background: {ACCENT_HOVER};
    border: 1px solid {ACCENT_HOVER};
}}

/* Ribbon tab bar ---------------------------------------------------------- */
QTabBar::tab {{
    padding: 6px 14px;
    border: 1px solid transparent;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    background: transparent;
    color: {TEXT_DIM};
}}
QTabBar::tab:selected {{
    color: {ACCENT_HOVER};
    border-bottom: 2px solid {ACCENT};
    background: {SURFACE};
}}
QTabBar::tab:hover {{
    color: {TEXT};
}}

/* Docks ------------------------------------------------------------------- */
QDockWidget {{
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: {SURFACE};
    padding: 4px 8px;
    border-bottom: 1px solid {BORDER};
}}
"""
