# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Main window — Phase 1 GUI skeleton."""
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLabel, QTabWidget, QToolBar,
)
from PySide6.QtCore import Qt

from ui.canvas import Canvas
from ui.lib import load_parts, cat_label


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKDev")
        self.resize(1280, 800)
        self._setup_log()         # must be first — others write to self._log
        self._setup_canvas()
        self._setup_parts_lib()
        self._setup_properties()
        self._setup_menu()        # creates self._a_build/_a_run/etc.
        self._setup_toolbar()     # reuses those actions

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
        dock.setMinimumHeight(120)
        tabs = QTabWidget()
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Log output…")
        tabs.addTab(self._log, "Log")
        self._editor = QTextEdit()
        self._editor.setPlaceholderText("Editor")
        tabs.addTab(self._editor, "Editor")
        dock.setWidget(tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

    def _setup_canvas(self):
        self._canvas = Canvas(log_fn=self._log.append)
        self.setCentralWidget(self._canvas)

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
        dock.setMinimumWidth(160)
        lbl = QLabel("(no selection)")
        lbl.setContentsMargins(8, 8, 8, 8)
        dock.setWidget(lbl)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _setup_menu(self):
        mb = self.menuBar()

        fm = mb.addMenu("File")
        fm.addAction(self._act("New Project",  "Ctrl+N"))
        fm.addAction(self._act("Open Project", "Ctrl+O"))
        fm.addAction(self._act("Save Project", "Ctrl+S"))
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
        tb.addAction(self._act("Save"))
        tb.addSeparator()
        tb.addAction(self._a_build)
        tb.addSeparator()
        tb.addAction(self._a_run)
        tb.addAction(self._a_pause)
        tb.addAction(self._a_step)
        tb.addAction(self._a_reset)
        self.addToolBar(tb)
