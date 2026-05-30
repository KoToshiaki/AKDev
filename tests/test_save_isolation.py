# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for project-scoped save isolation, filename validation, and sources field."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

from core.project import create_project, load_project, save_system
from ui.canvas import Canvas, PartNode
from ui.editor import EditorTabs, validate_source_name

_FAKE_PART = {"id": "ak32_cpu", "name": "AK32 CPU"}

# ---------------------------------------------------------------------------
# 4. Filename validation
# ---------------------------------------------------------------------------

def test_validate_empty_rejected():
    assert validate_source_name("", "asm") is not None
    assert validate_source_name("   ", "asm") is not None


def test_validate_absolute_path_rejected():
    assert validate_source_name("/etc/passwd.asm", "asm") is not None
    assert validate_source_name("C:\\evil.asm", "asm") is not None


def test_validate_dotdot_rejected():
    assert validate_source_name("../secret.asm", "asm") is not None


def test_validate_wrong_extension_rejected():
    assert validate_source_name("main.txt", "asm") is not None
    assert validate_source_name("main.asm", "v")   is not None
    assert validate_source_name("main",     "asm") is not None


def test_validate_forbidden_chars_rejected():
    for ch in '*?"<>|':
        assert validate_source_name(f"bad{ch}.asm", "asm") is not None, (
            f"expected '{ch}' to be rejected"
        )


def test_validate_valid_names_accepted():
    assert validate_source_name("main.asm",      "asm") is None
    assert validate_source_name("boot.asm",      "asm") is None
    assert validate_source_name("uart_test.asm", "asm") is None
    assert validate_source_name("cpu_core.v",    "v")   is None


# ---------------------------------------------------------------------------
# 5. EditorTabs: project_root guard and close_all_tabs
# ---------------------------------------------------------------------------

def test_open_tab_returns_none_without_project_root():
    tabs = EditorTabs()
    result = tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")
    assert result is None


def test_open_tab_saves_to_project_src(tmp_path):
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")

    from PySide6.QtWidgets import QTextEdit
    editor = tabs.currentWidget()
    assert isinstance(editor, QTextEdit)
    editor.setPlainText("NOP\nHALT")

    saved = tabs.save_current()
    assert saved is not None
    assert Path(saved) == (tmp_path / "src" / "main.asm").resolve() or \
           Path(saved) == tmp_path / "src" / "main.asm"
    assert (tmp_path / "src" / "main.asm").exists()
    assert (tmp_path / "src" / "main.asm").read_text(encoding="utf-8") == "NOP\nHALT"


def test_tab_name_is_source_name(tmp_path):
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "hello.asm")
    assert tabs.tabText(0) == "hello.asm"
    assert "node_0001" not in tabs.tabText(0)


def test_close_all_tabs(tmp_path):
    tabs = EditorTabs()
    tabs.set_project_root(tmp_path)
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")
    tabs.open_tab(_FAKE_PART, "node_0002", "v",   "top.v")
    assert tabs.count() == 2
    tabs.close_all_tabs()
    assert tabs.count() == 0
    assert len(tabs._open) == 0
    assert len(tabs._meta) == 0


# ---------------------------------------------------------------------------
# 8.1. Project isolation: A and B sources don't mix
# ---------------------------------------------------------------------------

def test_project_isolation(tmp_path):
    """Project A's main.asm must not appear when switching to Project B."""
    proj_a = tmp_path / "project_a"
    proj_b = tmp_path / "project_b"
    create_project(proj_a, "A")
    create_project(proj_b, "B")

    # Write main.asm in Project A.
    (proj_a / "src" / "main.asm").write_text("NOP\nHALT", encoding="utf-8")

    # Open a tab in Project A — content is loaded from disk.
    tabs = EditorTabs()
    tabs.set_project_root(proj_a)
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")
    from PySide6.QtWidgets import QTextEdit
    assert tabs.currentWidget().toPlainText() == "NOP\nHALT"

    # Switch to Project B and close all tabs.
    tabs.close_all_tabs()
    tabs.set_project_root(proj_b)

    # Open a tab with the same source_name in Project B — must be empty.
    tabs.open_tab(_FAKE_PART, "node_0001", "asm", "main.asm")
    assert tabs.currentWidget().toPlainText() == "", (
        "Project B's main.asm should be empty, not carry A's content"
    )


def test_build_out_isolated(tmp_path):
    """create_project creates build/out/ inside the project root."""
    root = create_project(tmp_path / "myproject", "Test")
    assert (root / "build" / "out").is_dir()


# ---------------------------------------------------------------------------
# 7. Canvas sources export / import
# ---------------------------------------------------------------------------

def test_export_parts_includes_sources(tmp_path):
    canvas = Canvas()
    part = {"id": "ak32_cpu", "name": "AK32 CPU", "category": "cpu"}
    canvas.add_part(part)
    node = next(i for i in canvas.scene().items() if isinstance(i, PartNode))
    node.set_source("asm", "src/main.asm")

    exported = canvas.export_parts()
    assert len(exported) == 1
    assert exported[0]["sources"] == {"asm": "src/main.asm", "hdl": None}


def test_import_parts_restores_sources(tmp_path):
    parts_data = [
        {
            "node_id": "node_0001",
            "part_id": "ak32_cpu",
            "name":    "AK32 CPU",
            "x":       0.0,
            "y":       0.0,
            "sources": {"asm": "src/main.asm", "hdl": None},
        }
    ]
    part_lib = {"ak32_cpu": {"id": "ak32_cpu", "name": "AK32 CPU", "category": "cpu"}}
    canvas = Canvas()
    canvas.import_parts(parts_data, part_lib)

    nodes = [i for i in canvas.scene().items() if isinstance(i, PartNode)]
    assert len(nodes) == 1
    assert nodes[0].sources() == {"asm": "src/main.asm", "hdl": None}


def test_import_parts_missing_sources_defaults(tmp_path):
    """Parts without a 'sources' field default to {asm: null, hdl: null}."""
    parts_data = [
        {"node_id": "node_0001", "part_id": "ak32_cpu",
         "name": "AK32 CPU", "x": 0.0, "y": 0.0},
    ]
    part_lib = {"ak32_cpu": {"id": "ak32_cpu", "name": "AK32 CPU", "category": "cpu"}}
    canvas = Canvas()
    canvas.import_parts(parts_data, part_lib)
    nodes = [i for i in canvas.scene().items() if isinstance(i, PartNode)]
    assert nodes[0].sources() == {"asm": None, "hdl": None}


# ---------------------------------------------------------------------------
# 8.2. system.json sources round-trip
# ---------------------------------------------------------------------------

def test_system_json_sources_saved_and_restored(tmp_path):
    """sources.asm persists across save/load of system.json."""
    root = create_project(tmp_path / "proj", "Test")

    canvas = Canvas()
    part = {"id": "ak32_cpu", "name": "AK32 CPU", "category": "cpu"}
    canvas.add_part(part)
    node = canvas.get_node("node_0001")
    assert node is not None
    node.set_source("asm", "src/main.asm")

    # Save
    _, system = load_project(root)
    system["parts"] = canvas.export_parts()
    save_system(root, system)

    # Reload
    _, loaded = load_project(root)
    assert loaded["parts"][0]["sources"]["asm"] == "src/main.asm"
    assert loaded["parts"][0]["sources"]["hdl"] is None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        with tempfile.TemporaryDirectory() as d:
            try:
                fn(Path(d))
                print(f"  PASS  {fn.__name__}")
                passed += 1
            except Exception as exc:
                print(f"  FAIL  {fn.__name__}: {exc}")
                import traceback; traceback.print_exc()
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
