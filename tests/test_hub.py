# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Headless tests: AKDev Hub entry screen."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from ui.hub import HubWindow


def test_hub_instantiates():
    hub = HubWindow()
    assert hub.windowTitle().startswith("AKDev")


def test_hub_has_new_and_open_buttons():
    hub = HubWindow()
    assert hub._btn_new.text() == "+  New Project"
    assert hub._btn_open.text() == "Open Project"


def test_hub_new_button_emits_signal():
    hub = HubWindow()
    fired = []
    hub.new_project_requested.connect(lambda: fired.append(True))
    hub._btn_new.click()
    assert fired == [True]


def test_hub_open_button_emits_signal():
    hub = HubWindow()
    fired = []
    hub.open_project_requested.connect(lambda: fired.append(True))
    hub._btn_open.click()
    assert fired == [True]


def test_hub_has_recent_placeholder():
    hub = HubWindow()
    assert "なし" in hub._recent.text()


def test_hub_has_template_cards():
    hub = HubWindow()
    titles = hub.template_titles()
    assert "AK32 Baremetal" in titles
    assert "Empty" in titles
    assert len(titles) >= 3


def test_hub_coming_soon_card_disabled():
    hub = HubWindow()
    coming = [c for c in hub._template_cards if c.title == "Coming soon"]
    assert coming and not coming[0].isEnabled()
