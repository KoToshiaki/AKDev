# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
import json
import tempfile
from pathlib import Path

import pytest

from core.project import (
    create_project,
    default_target_config,
    default_tools_config,
    load_json_or_default,
)


@pytest.fixture()
def proj(tmp_path):
    return create_project(tmp_path / "myproj", "myproj")


def test_target_json_created(proj):
    assert (proj / "target.json").exists()


def test_tools_json_created(proj):
    assert (proj / "tools.json").exists()


def test_hdl_dir_created(proj):
    assert (proj / "hdl").is_dir()


def test_board_dir_created(proj):
    assert (proj / "board").is_dir()


def test_docs_dir_created(proj):
    assert (proj / "docs").is_dir()


def test_build_out_created(proj):
    assert (proj / "build" / "out").is_dir()


def test_build_rom_created(proj):
    assert (proj / "build" / "rom").is_dir()


def test_build_export_created(proj):
    assert (proj / "build" / "export").is_dir()


def test_vscode_settings_created(proj):
    assert (proj / ".vscode" / "settings.json").exists()


def test_vscode_extensions_created(proj):
    assert (proj / ".vscode" / "extensions.json").exists()


def test_target_json_default_name(proj):
    data = json.loads((proj / "target.json").read_text(encoding="utf-8"))
    assert data["target"]["name"] == "AK32 Baremetal"


def test_target_json_build_type(proj):
    data = json.loads((proj / "target.json").read_text(encoding="utf-8"))
    assert data["build"]["type"] == "internal_assembler"


def test_tools_json_vscode(proj):
    data = json.loads((proj / "tools.json").read_text(encoding="utf-8"))
    assert "vscode" in data["tools"]
    assert data["tools"]["vscode"]["command"] == "code"


def test_tools_json_kicad_slot(proj):
    data = json.loads((proj / "tools.json").read_text(encoding="utf-8"))
    assert "kicad" in data["tools"]
    assert data["tools"]["kicad"]["enabled"] is False


def test_extensions_json_recommendation(proj):
    data = json.loads((proj / ".vscode" / "extensions.json").read_text(encoding="utf-8"))
    assert "akdev.akdev-companion" in data["recommendations"]


def test_load_json_or_default_missing():
    result = load_json_or_default(Path("/nonexistent/target.json"), default_target_config)
    assert result["target"]["name"] == "AK32 Baremetal"


def test_load_json_or_default_existing(tmp_path):
    p = tmp_path / "custom.json"
    p.write_text('{"custom": true}', encoding="utf-8")
    result = load_json_or_default(p, default_target_config)
    assert result == {"custom": True}
