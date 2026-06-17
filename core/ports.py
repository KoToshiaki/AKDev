# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Port schema normalization (PATCH_PORT_SCHEMA_V08).

part.json historically described each port as ``{"name", "type"}`` only.  v0.8's
connection validation needs an explicit, single source of truth for a port's
``role`` / ``direction`` / ``width``, so this module defines the v2 port schema and
a normalization layer that:

  * preserves explicit v2 fields, and
  * fills missing fields for legacy (v1) parts by deriving them from ``type``
    (and, for ``irq``, from the owning part — a CPU *consumes* an interrupt while a
    peripheral *produces* one, so its direction is part-specific).

The functions are pure (dict in, dict out) so they can be unit-tested and reused by
the parts library loader, Port Detail, and future validation without divergence.

This module performs **no validation / blocking** — it only normalizes the schema.
"""
from __future__ import annotations

SCHEMA_VERSION = 2

_BUS_WIDTH    = 32
_SIGNAL_WIDTH = 1
_VIDEO_WIDTH  = 24

# Single-bit point signals (width 1).
_SIGNAL_KINDS = ("clock", "reset", "irq", "serial", "gpio")


def base_port_type(port_type: "str | None") -> str:
    """Return the base kind of a (possibly dotted) port type.

    ``"bus.master" -> "bus"``, ``"serial.uart" -> "serial"``, ``"clock" -> "clock"``.
    Empty / None -> ``""``.
    """
    t = (port_type or "").strip().lower()
    if not t:
        return ""
    return t.split(".", 1)[0]


def _is_cpu_part(part_id: "str | None") -> bool:
    """True if a part id denotes a CPU (consumes IRQ rather than producing it)."""
    return base_port_type(part_id) == "cpu"


def derive_role(port_type: "str | None") -> "str | None":
    """Infer the bus role from a port type. Non-bus ports have no role (None)."""
    t = (port_type or "").lower()
    if base_port_type(t) != "bus":
        return None
    if "master" in t:
        return "master"
    if "slave" in t:
        return "slave"
    return None


def derive_direction(port_type: "str | None", *,
                     part_id: "str | None" = None,
                     port_name: "str | None" = None) -> str:
    """Infer a port direction from its type (and owning part for IRQ).

    Returns one of ``"in"`` / ``"out"`` / ``"inout"``. Unknown types fall back to
    ``"inout"`` (the safe, permissive default).
    """
    base = base_port_type(port_type)
    if base == "irq":
        # Part-specific: a CPU consumes interrupts (in); peripherals produce them (out).
        return "in" if _is_cpu_part(part_id) else "out"
    if base == "bus":
        return "inout"
    if base in ("clock", "reset"):
        return "in"
    if base == "serial":
        return "inout"
    if base == "gpio":
        return "inout"
    if base == "video":
        return "out"
    return "inout"


def derive_width(port_type: "str | None") -> "int | None":
    """Infer a port's signal width (bits) from its type. Unknown -> None."""
    base = base_port_type(port_type)
    if base == "bus":
        return _BUS_WIDTH
    if base in _SIGNAL_KINDS:
        return _SIGNAL_WIDTH
    if base == "video":
        return _VIDEO_WIDTH
    return None


def normalize_port(port: dict, *, part_id: "str | None" = None) -> dict:
    """Return a v2-normalized copy of a single port dict.

    Explicit fields are preserved; only missing ones are derived. Safe on unknown
    types and on dicts missing ``name`` / ``type``.
    """
    p = dict(port or {})
    ptype = p.get("type", "")
    name  = p.get("name", "")
    if "role" not in p:
        p["role"] = derive_role(ptype)
    if "direction" not in p:
        p["direction"] = derive_direction(ptype, part_id=part_id, port_name=name)
    if "width" not in p:
        p["width"] = derive_width(ptype)
    if "required" not in p:
        # IRQ lines are optional by nature; everything else defaults to required.
        p["required"] = base_port_type(ptype) != "irq"
    if "description" not in p:
        p["description"] = ""
    return p


def normalize_ports(ports: "list[dict] | None", *,
                    part_id: "str | None" = None) -> list:
    """Return a list of v2-normalized port dicts."""
    return [normalize_port(p, part_id=part_id) for p in (ports or [])]


def normalize_part(part: dict) -> dict:
    """Return a v2-normalized copy of a part dict.

    Ports are normalized and ``schema_version`` is set to :data:`SCHEMA_VERSION`.
    A part without ``schema_version`` is treated as v1 and upgraded in place; an
    already-v2 part keeps its explicit values (normalization is idempotent). Other
    top-level keys (``editable`` / ``resources`` / ...) are preserved unchanged.
    """
    if not isinstance(part, dict):
        return part
    out = dict(part)
    out["ports"] = normalize_ports(out.get("ports", []), part_id=out.get("id"))
    out["schema_version"] = SCHEMA_VERSION
    return out


def is_legacy_part(part: dict) -> bool:
    """True if *part* predates the v2 schema (no ``schema_version`` key)."""
    return isinstance(part, dict) and "schema_version" not in part
