# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Project creation and file management."""
import json
from datetime import datetime, timezone
from pathlib import Path

AKDEV_VERSION = "0.1.0"


def default_target_config() -> dict:
    return {
        "target": {
            "name": "AK32 Baremetal",
            "isa": "ak32",
            "cpu": "ak32",
            "runtime": "baremetal",
            "entry": "src/main.asm",
            "output": "build/out/main.bin",
            "load_address": "0x0000",
            "entry_point": "0x0000",
        },
        "build": {
            "type": "internal_assembler",
            "input": "src/main.asm",
            "output": "build/out/main.bin",
        },
    }


def default_tools_config() -> dict:
    return {
        "tools": {
            "vscode": {
                "command": "code",
                "args": ["{project_root}"],
            },
            "kicad": {
                "command": "kicad",
                "args": ["{project_root}/board/{project_name}.kicad_pro"],
                "enabled": False,
            },
        }
    }


def create_project(path: "str | Path", name: str, preset: str = "empty") -> Path:
    """Create a new project directory with initial files and subdirectories.

    Raises FileExistsError if the path already exists.
    Returns the project root as a Path.
    """
    root = Path(path)
    if root.exists():
        raise FileExistsError(f"Project path already exists: {root}")

    # ---- directory structure ----
    root.mkdir(parents=True)
    (root / "src").mkdir()
    (root / "hdl").mkdir()
    (root / "board").mkdir()
    (root / "asset").mkdir()
    (root / "docs").mkdir()
    (root / "build").mkdir()
    (root / "build" / "out").mkdir()
    (root / "build" / "rom").mkdir()
    (root / "build" / "export").mkdir()
    (root / "parts" / "custom").mkdir(parents=True)
    vscode = root / ".vscode"
    vscode.mkdir()

    # ---- project.json ----
    _write_json(root / "project.json", {
        "name":          name,
        "created_at":    datetime.now(timezone.utc).isoformat(),
        "akdev_version": AKDEV_VERSION,
        "preset":        preset,
        "last_file":     "",
    })

    # ---- system.json ----
    _write_json(root / "system.json", {
        "chips":      [],
        "parts":      [],
        "links":      [],
        "memory_map": [],
    })

    # ---- target.json ----
    _write_json(root / "target.json", default_target_config())

    # ---- tools.json ----
    _write_json(root / "tools.json", default_tools_config())

    # ---- .vscode/settings.json ----
    _write_json(vscode / "settings.json", {"akdev.project": True})

    # ---- .vscode/extensions.json ----
    _write_json(vscode / "extensions.json", {
        "recommendations": ["akdev.akdev-companion"]
    })

    return root


def save_system(root: "str | Path", system_data: dict) -> None:
    """Overwrite system.json in an existing project root."""
    _write_json(Path(root) / "system.json", system_data)


def load_project(root: "str | Path") -> tuple[dict, dict]:
    """Load project.json and system.json from an existing project root.

    Returns (project_data, system_data).
    Raises FileNotFoundError or json.JSONDecodeError on bad input.
    """
    root = Path(root)
    project = _read_json(root / "project.json")
    system  = _read_json(root / "system.json")
    return project, system


def load_json_or_default(path: "str | Path", default_fn) -> dict:
    """Read a JSON file, or return default_fn() if the file does not exist."""
    p = Path(path)
    if p.exists():
        return _read_json(p)
    return default_fn()


def load_target(root: "str | Path") -> dict:
    """Load target.json from project root, or return AK32 Baremetal default."""
    return load_json_or_default(Path(root) / "target.json", default_target_config)


def load_tools(root: "str | Path") -> dict:
    """Load tools.json from project root, or return default tools config."""
    return load_json_or_default(Path(root) / "tools.json", default_tools_config)


_EXT_TO_SRC_TYPE: dict[str, str] = {
    ".asm": "asm",
    ".v":   "hdl",
    ".vhd": "hdl",
    ".c":   "c",
    ".cpp": "cpp",
    ".cc":  "cpp",
    ".cxx": "cpp",
    ".ld":  "linker",
    ".bin": "binary",
    ".hex": "binary",
}


def src_type(path: "str | Path") -> str:
    """Return source type for a file based on its extension."""
    ext = Path(path).suffix.lower()
    return _EXT_TO_SRC_TYPE.get(ext, "custom")


# ------------------------------------------------------------------ helpers

def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
