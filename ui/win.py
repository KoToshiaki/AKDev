# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Main window."""
import shutil
from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QToolBar, QSplitter,
)
from PySide6.QtCore import Qt

from asm.asm import AsmError, assemble
from core.cpu import AK32Part
from core.dev import RamPart, UartPart
from core.project import create_project, load_project, save_system
from core.sim import Bus
from ui.canvas import Canvas
from ui.editor import EditorTabs
from ui.lib import load_parts, cat_label
from ui.prop import PropPanel

_DEFAULT_PROJECT = Path("build/current_project")
_BUILD_OUT       = Path("build/out")

# Minimal simulation memory map (kept within 16-bit immediate range for LDI).
_SIM_RAM_BASE  = 0x0000
_SIM_RAM_SIZE  = 0x0100   # 256 bytes — ends at 0x00FF
_SIM_UART_BASE = 0x0100
_SIM_UART_SIZE = 8


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKDev")
        self.resize(1280, 800)
        self._project_root: Path | None = None
        self._setup_log()          # must be first — others write to self._log
        self._setup_sim()          # creates self._sim_bus/ram/uart/cpu
        self._setup_canvas()       # creates self._canvas and self._editor_tabs
        self._setup_parts_lib()
        self._setup_properties()   # creates self._prop_panel
        self._canvas.selection_changed.connect(self._on_canvas_selection)
        self._canvas.tab_open_requested.connect(self._on_open_tab)
        self._setup_menu()         # creates self._a_new/_a_open/_a_save/etc.
        self._setup_toolbar()      # reuses those actions

    # ------------------------------------------------------------------ sim setup

    def _setup_sim(self):
        self._sim_bus  = Bus()
        self._sim_ram  = RamPart("sim_ram",  "RAM",  size=_SIM_RAM_SIZE,  base=_SIM_RAM_BASE)
        self._sim_uart = UartPart("sim_uart", "UART", base=_SIM_UART_BASE)
        self._sim_cpu  = AK32Part("sim_cpu",  "AK32", self._sim_bus, reset_pc=_SIM_RAM_BASE)
        self._sim_bus.attach(self._sim_ram,  _SIM_RAM_BASE,  _SIM_RAM_SIZE)
        self._sim_bus.attach(self._sim_uart, _SIM_UART_BASE, _SIM_UART_SIZE)

    # ------------------------------------------------------------------ helpers

    def _act(self, text, shortcut=None):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(lambda: self._log.append(f"Action: {text}"))
        return a

    # ------------------------------------------------------------------ setup

    def _setup_log(self):
        dock = QDockWidget("Log / Console", self)
        dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        dock.setMinimumHeight(100)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Log output…")
        dock.setWidget(self._log)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

    def _setup_canvas(self):
        self._canvas = Canvas(log_fn=self._log.append)
        self._editor_tabs = EditorTabs()
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._canvas)
        splitter.addWidget(self._editor_tabs)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def _setup_parts_lib(self):
        dock = QDockWidget("Parts Library", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setMinimumWidth(160)
        self._parts_tree = QTreeWidget()
        self._parts_tree.setHeaderHidden(True)

        cats, errors = load_parts()
        for cat_key, parts in cats.items():
            cat_item = QTreeWidgetItem(self._parts_tree, [cat_label(cat_key)])
            for p in parts:
                child = QTreeWidgetItem(cat_item, [p["name"]])
                child.setData(0, Qt.UserRole, p)
        self._parts_tree.expandAll()
        self._parts_tree.itemDoubleClicked.connect(self._on_part_dbl_click)

        for err in errors:
            self._log.append(err)

        dock.setWidget(self._parts_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    def _on_part_dbl_click(self, item, _col):
        part = item.data(0, Qt.UserRole)
        if part:
            self._canvas.add_part(part)

    def _setup_properties(self):
        dock = QDockWidget("Properties", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setMinimumWidth(180)
        self._prop_panel = PropPanel()
        dock.setWidget(self._prop_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _on_canvas_selection(self, nodes: list):
        if not nodes:
            self._prop_panel.show_none()
        elif len(nodes) == 1:
            n = nodes[0]
            self._prop_panel.show_part(n.part(), n.node_id())
        else:
            self._prop_panel.show_multi(len(nodes))

    def _on_open_tab(self, part: dict, node_id: str, ext: str):
        tab_name = self._editor_tabs.open_tab(part, node_id, ext)
        if tab_name:
            self._log.append(f"Opened tab: {tab_name}")

    def _part_library(self) -> dict:
        """Return {part_id: part_dict} for all loaded parts."""
        cats, _ = load_parts()
        return {p["id"]: p for parts in cats.values() for p in parts}

    def _ensure_project_root(self) -> Path:
        """Return the current project root, creating the default one if needed."""
        if self._project_root is not None:
            return self._project_root
        root = _DEFAULT_PROJECT
        if not root.exists():
            create_project(root, "Current Project")
        self._project_root = root
        return root

    def _new_project(self):
        root = _DEFAULT_PROJECT
        if root.exists():
            shutil.rmtree(root)
        create_project(root, "New Project")
        self._project_root = root
        self._canvas.import_parts([], {})   # clear canvas
        self._log.append(f"New project: {root.as_posix()}")

    def _open_project(self):
        root = _DEFAULT_PROJECT
        if not (root / "project.json").exists():
            self._log.append(f"Open: no project found at {root.as_posix()}")
            return
        try:
            project, system = load_project(root)
        except Exception as exc:
            self._log.append(f"Open failed: {exc}")
            return
        self._canvas.import_parts(system.get("parts", []), self._part_library())
        self._project_root = root
        self._log.append(
            f"Opened project: {root.as_posix()}  [{project.get('name', '?')}]"
        )

    def _save_project(self):
        root = self._ensure_project_root()
        try:
            _, system = load_project(root)
        except Exception:
            system = {"chips": [], "parts": [], "links": [], "memory_map": []}
        system["parts"] = self._canvas.export_parts()
        save_system(root, system)
        # also flush the active editor tab
        tab_path = self._editor_tabs.save_current()
        if tab_path:
            self._log.append(f"Saved: {tab_path}")
        self._log.append(f"Saved project: {root.as_posix()}")

    def _build(self):
        tab = self._editor_tabs.current_tab_info()
        if tab is None or tab.ext != "asm":
            self._log.append("Build: current tab is not an asm file")
            return
        try:
            binary = assemble(tab.text)
        except AsmError as exc:
            self._log.append(f"Build FAILED: {exc}")
            return
        _BUILD_OUT.mkdir(parents=True, exist_ok=True)
        out_path = _BUILD_OUT / f"{tab.node_id}.bin"
        out_path.write_bytes(binary)
        self._log.append(
            f"Build succeeded: {out_path.as_posix()}  ({len(binary)} bytes)"
        )
        # Load binary into simulator RAM and reset the CPU.
        self._sim_ram.reset()
        self._sim_ram.load_bytes(binary)
        self._sim_uart.reset()
        self._sim_cpu.reset()
        self._log.append(f"Loaded binary to RAM: {len(binary)} bytes")

    def _setup_menu(self):
        mb = self.menuBar()

        self._a_new  = QAction("New Project",  self)
        self._a_new.setShortcut(QKeySequence("Ctrl+N"))
        self._a_new.triggered.connect(self._new_project)

        self._a_open = QAction("Open Project", self)
        self._a_open.setShortcut(QKeySequence("Ctrl+O"))
        self._a_open.triggered.connect(self._open_project)

        self._a_save = QAction("Save Project", self)
        self._a_save.setShortcut(QKeySequence("Ctrl+S"))
        self._a_save.triggered.connect(self._save_project)

        fm = mb.addMenu("File")
        fm.addAction(self._a_new)
        fm.addAction(self._a_open)
        fm.addAction(self._a_save)
        fm.addSeparator()
        fm.addAction(self._act("Exit", "Ctrl+Q"))

        bm = mb.addMenu("Build")
        self._a_build = QAction("Build", self)
        self._a_build.setShortcut(QKeySequence("F5"))
        self._a_build.triggered.connect(self._build)
        bm.addAction(self._a_build)

        rm = mb.addMenu("Run")
        self._a_run   = self._act("Run",   "Ctrl+R")
        self._a_pause = self._act("Pause", "F6")
        self._a_step  = self._act("Step",  "F10")
        self._a_reset = self._act("Reset", "Ctrl+Shift+R")
        for a in (self._a_run, self._a_pause, self._a_step, self._a_reset):
            rm.addAction(a)

        vm = mb.addMenu("View")
        vm.addAction(self._act("Bus Trace"))
        vm.addAction(self._act("Memory"))
        vm.addAction(self._act("Registers"))

    def _setup_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.addAction(self._a_new)
        tb.addAction(self._a_open)
        tb.addAction(self._a_save)
        tb.addSeparator()
        tb.addAction(self._a_build)
        tb.addSeparator()
        tb.addAction(self._a_run)
        tb.addAction(self._a_pause)
        tb.addAction(self._a_step)
        tb.addAction(self._a_reset)
        self.addToolBar(tb)
