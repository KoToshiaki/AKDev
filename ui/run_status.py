# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Run Status panel — a read-only summary of the current execution state.

PATCH_RUN_STATUS_PANEL_V07: target CPU / connected RAM-UART / Address Map /
loaded program / PC-cycle-halted / last trace / UART output are spread across the
Log and several debug panels.  This panel gathers a snapshot dict (built by
MainWin from existing state) and renders it in one place.  It owns no execution
state — it only formats what it is given, defensively (missing keys are fine).
"""
from __future__ import annotations

from PySide6.QtWidgets import QDockWidget, QPlainTextEdit, QWidget
from PySide6.QtCore import Qt


def _fmt_program(prog: "dict | None") -> list[str]:
    if not prog:
        return ["Program", "  Loaded: No"]
    lines = ["Program", "  Loaded: Yes"]
    path = prog.get("path")
    if path:
        lines.append(f"  Path: {path}")
    if prog.get("target_node_id"):
        lines.append(f"  Target node: {prog['target_node_id']}")
    if prog.get("source_type"):
        lines.append(f"  Source type: {prog['source_type']}")
    if prog.get("status"):
        lines.append(f"  Status: {prog['status']}")
    if prog.get("size") is not None:
        lines.append(f"  Size: {prog['size']} bytes")
    return lines


def _fmt_trace(trace: "dict | None") -> list[str]:
    lines = ["Trace summary"]
    if not trace:
        lines.append("  (no trace yet)")
        return lines
    mem = trace.get("memory") or []
    io  = trace.get("io") or []
    reg = trace.get("register_changes") or {}
    if mem:
        for m in mem:
            arrow = "<-" if m.get("type") == "write" else "->"
            lines.append(f"  MEM {m.get('type', '?').upper()} {m.get('addr')} {arrow} {m.get('value')}")
    else:
        lines.append("  MEM: (none)")
    if io:
        for i in io:
            arrow = "<-" if i.get("type") == "write" else "->"
            lines.append(
                f"  IO {i.get('type', '?').upper()} {i.get('addr')} {arrow} "
                f"{i.get('value')} ({i.get('device')})"
            )
    else:
        lines.append("  IO: (none)")
    if reg:
        for name, ba in reg.items():
            try:
                before, after = ba
            except (ValueError, TypeError):
                before, after = "?", "?"
            lines.append(f"  REG {name}: {before} -> {after}")
    else:
        lines.append("  REG: (none)")
    return lines


def render_status(status: dict) -> str:
    """Render a status dict into a human-readable multi-line string."""
    status = status or {}
    mode = status.get("mode", "legacy")
    lines: list[str] = ["=== Run Status ===", f"Mode: {mode}"]
    # PATCH_PROGRAM_TARGET_ROM_V08: show the current Write Program load target.
    lines.append(f"Program Target: {status.get('program_target', 'RAM')}")
    # PATCH_TIMER_DEVICE_V08: show Timer tick/delta when a Timer device is placed.
    timer = status.get("timer")
    if timer:
        lines.append(
            f"Timer: tick={timer.get('tick', 0)} delta={timer.get('delta', 0)}"
            f" @0x{timer.get('base', 0):04x}"
        )
    else:
        lines.append("Timer: None")
    # PATCH_VRAM_DEVICE_V08: show VRAM base/size when a VRAM device is placed.
    vram = status.get("vram")
    if vram:
        lines.append(
            f"VRAM: base=0x{vram.get('base', 0):04x} size=0x{vram.get('size', 0):04x}"
        )
    else:
        lines.append("VRAM: None")
    # PATCH_GAME_RUNTIME_MINIMAL_V08: minimal game-runtime indicator (ROM/Input/Timer/VRAM).
    game = status.get("game")
    lines.append(f"Game: {game}" if game else "Game: None")

    # ---- Target / Circuit ----
    lines.append(f"Target CPU: {status.get('target_cpu') or 'None'}")
    lines.append(f"RAM: {status.get('ram_desc', '(none)')}")
    lines.append(f"UART: {status.get('uart_desc', '(none)')}")
    issues = status.get("issues") or []
    if issues:
        lines.append("Issues:")
        for s in issues:
            lines.append(f"  - {s}")
    else:
        lines.append("Issues: (none)")
    lines.append("")

    # ---- Program ----
    lines += _fmt_program(status.get("program"))
    lines.append("")

    # ---- Runtime ----
    pc = status.get("pc")
    pc_str = f"0x{pc:04x}" if isinstance(pc, int) else "----"
    lines.append("Runtime")
    lines.append(f"  PC: {pc_str}")
    lines.append(f"  Cycle: {status.get('cycle', 0)}")
    lines.append(f"  Halted: {'yes' if status.get('halted') else 'no'}")
    lines.append(f"  Step count: {status.get('step_count', 0)}")
    trace = status.get("last_trace")
    if trace:
        lines.append(f"  Last instruction: {trace.get('instruction', '-')}")
        pb, pa = trace.get("pc_before"), trace.get("pc_after")
        if isinstance(pb, int) and isinstance(pa, int):
            lines.append(f"  PC before -> after: 0x{pb:04x} -> 0x{pa:04x}")
    else:
        lines.append("  Last instruction: (none)")
    lines.append("")

    # ---- Address Map ----
    amap_lines = status.get("address_map_lines") or []
    if amap_lines:
        lines += amap_lines
    else:
        lines.append("Address Map: (none)")
    for issue in status.get("address_map_issues") or []:
        lines.append(f"  Address Map issue: {issue}")
    lines.append("")

    # ---- UART ----
    uart = status.get("uart_out", "")
    lines.append(f"UART output: {uart!r}" if uart else "UART output: (none)")
    lines.append("")

    # ---- Trace summary ----
    lines += _fmt_trace(trace)
    return "\n".join(lines)


class RunStatusPanel(QDockWidget):
    """Dock panel that shows a summary of the current run/execution state."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Run Status", parent)
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
            | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea
        )
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setPlaceholderText("Run status will appear here...")
        font = self._text.font()
        font.setFamily("Courier New")
        font.setPointSize(9)
        self._text.setFont(font)
        self.setWidget(self._text)
        self._status: dict = {}

    # ------------------------------------------------------------------ public

    def update_status(self, status: dict) -> None:
        """Refresh the panel from a status snapshot dict."""
        self._status = dict(status or {})
        self._text.setPlainText(render_status(self._status))

    def status_text(self) -> str:
        """Return the current rendered status text (for tests / inspection)."""
        return self._text.toPlainText()
