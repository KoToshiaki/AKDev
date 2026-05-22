# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Project creation and file management."""
import json
from datetime import datetime, timezone
from pathlib import Path

AKDEV_VERSION = "0.1.0"


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
    (root / "asset").mkdir()
    (root / "build").mkdir()
    (root / "parts" / "custom").mkdir(parents=True)

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

    return root


def load_project(root: "str | Path") -> tuple[dict, dict]:
    """Load project.json and system.json from an existing project root.

    Returns (project_data, system_data).
    Raises FileNotFoundError or json.JSONDecodeError on bad input.
    """
    root = Path(root)
    project = _read_json(root / "project.json")
    system  = _read_json(root / "system.json")
    return project, system


# ------------------------------------------------------------------ helpers

def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
