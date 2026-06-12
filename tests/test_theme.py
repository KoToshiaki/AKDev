# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests: visual identity theme constants and stylesheet."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ui import theme


def test_accent_is_hex_color():
    assert theme.ACCENT.startswith("#")
    assert len(theme.ACCENT) == 7


def test_app_name_is_akdev():
    assert theme.APP_NAME == "AKDev"


def test_tagline_mentions_environment():
    assert "Development Environment" in theme.APP_TAGLINE


def test_stylesheet_is_nonempty_string():
    assert isinstance(theme.STYLESHEET, str)
    assert len(theme.STYLESHEET) > 0


def test_stylesheet_uses_accent():
    assert theme.ACCENT in theme.STYLESHEET
