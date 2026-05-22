# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Parts library loader — scans parts/ and returns categorised part definitions."""
import json
import pathlib
from collections import defaultdict

_REQUIRED = {"id", "name", "category", "ports"}

_PARTS_DIR = pathlib.Path(__file__).parent.parent / "parts"

_CAT_LABEL = {
    "fpga":   "FPGA",
    "cpu":    "CPU",
    "mem":    "Memory",
    "io":     "I/O",
    "video":  "Video",
    "bus":    "Bus",
    "debug":  "Debug",
    "custom": "Custom",
}
_CAT_ORDER = list(_CAT_LABEL.keys())


def load_parts():
    """Return (cats, errors).

    cats   — dict {category_key: [part_dict, ...]} sorted by _CAT_ORDER
    errors — list of error strings for invalid/unreadable part.json files
    """
    cats = defaultdict(list)
    errors = []
    for path in sorted(_PARTS_DIR.rglob("part.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            missing = _REQUIRED - data.keys()
            if missing:
                raise ValueError(f"missing keys: {', '.join(sorted(missing))}")
            cats[data["category"]].append(data)
        except Exception as exc:
            errors.append(f"[lib] {path.relative_to(_PARTS_DIR)}: {exc}")
    ordered = {k: cats[k] for k in _CAT_ORDER if k in cats}
    for k in sorted(cats):
        if k not in ordered:
            ordered[k] = cats[k]
    return ordered, errors


def cat_label(key: str) -> str:
    return _CAT_LABEL.get(key, key.capitalize())
