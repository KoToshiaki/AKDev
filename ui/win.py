# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Main window — Phase 1 GUI skeleton."""
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QToolBar, QSplitter,
)
from PySide6.QtCore import Qt

from ui.canvas import Canvas
from ui.editor import EditorTabs
from ui.lib import load_parts, cat_label
from ui.prop import PropPanel


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKDev")
        self.resize(1280, 800)
        self._setup_log()          # must be first — others write to self._log
        self._setup_canvas()       # creates self._canvas and self._editor_tabs
        self._setup_parts_lib()
        self._setup_properties()   # creates self._prop_panel
        self._canvas.selection_changed.connect(self._on_canvas_selection)
        self._canvas.tab_open_requested.connect(self._on_open_tab)
        self._setup_menu()         # creates self._a_build/_a_run/etc.
        self._setup_toolbar()      # reuses those actions

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

    def _save_current_tab(self):
        save_path = self._editor_tabs.save_current()
        if save_path:
            self._log.append(f"Saved: {save_path}")
        else:
            self._log.append("Save: no editor tab active")

    def _setup_menu(self):
        mb = self.menuBar()

        # Save action shared by menu and toolbar (Ctrl+S)
        self._a_save = QAction("Save Project", self)
        self._a_save.setShortcut(QKeySequence("Ctrl+S"))
        self._a_save.triggered.connect(self._save_current_tab)

        fm = mb.addMenu("File")
        fm.addAction(self._act("New Project",  "Ctrl+N"))
        fm.addAction(self._act("Open Project", "Ctrl+O"))
        fm.addAction(self._a_save)
        fm.addSeparator()
        fm.addAction(self._act("Exit", "Ctrl+Q"))

        bm = mb.addMenu("Build")
        self._a_build = self._act("Build", "F5")
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
        tb.addAction(self._act("New"))
        tb.addAction(self._act("Open"))
        tb.addAction(self._a_save)   # reuse: triggers Ctrl+S / _save_current_tab
        tb.addSeparator()
        tb.addAction(self._a_build)
        tb.addSeparator()
        tb.addAction(self._a_run)
        tb.addAction(self._a_pause)
        tb.addAction(self._a_step)
        tb.addAction(self._a_reset)
        self.addToolBar(tb)
