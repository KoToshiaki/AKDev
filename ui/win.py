# SPDX-FileCopyrightText: 2026 Toshiaki Kou
# SPDX-License-Identifier: BSD-3-Clause
"""Main window."""
from pathlib import Path

from PySide6.QtGui import QAction, QDrag, QKeySequence, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QToolBar, QSplitter, QInputDialog, QFileDialog,
)
from PySide6.QtCore import Qt, QMimeData, QUrl

from asm.asm import AsmError, assemble_ex
from core.circuit import (
    resolve_circuit,
    build_address_map_from_devices,
    validate_address_map,
    format_address_map_summary,
    validate_address_overrides,
)
from core.devices import (
    make_device_spec, legacy_device_specs, assign_mmio_bases, multi_device_warnings,
    get_memory_layout, apply_address_overrides,
)
from core.cpu import AK32Part
from core.dev import RamPart, RomPart, UartPart, InputPart
from core.project import create_project, load_project, load_target, save_system
from core.runtime import VirtualCircuitRuntime
from core.sim import Bus
from ui.canvas import Canvas
from ui.editor import EditorTabs, validate_source_name
from ui.lib import load_parts, cat_label
from ui.memview import MemoryViewer
from ui.prop import PropPanel
from ui.ribbon import RibbonBar
from ui.run_status import RunStatusPanel
from ui.port_detail import PortDetailPanel, build_node_info, build_wire_info
from ui.address_map_editor import AddressMapEditor

# Minimal simulation memory map (kept within 16-bit immediate range for LDI).
# Canonical values live in core/devices.py and are imported here so the device
# registry and MainWin share one source (PATCH_DEVICE_REGISTRY_REFACTOR_V08).
# circuit mode: RAM fills the whole 16-bit space (64 KB) with the UART as an MMIO
# window at 0x0100; legacy mode keeps the fixed 256-byte RAM.
from core.devices import (
    RAM_BASE         as _SIM_RAM_BASE,
    LEGACY_RAM_SIZE  as _SIM_RAM_SIZE,
    UART_BASE        as _SIM_UART_BASE,
    UART_SIZE        as _SIM_UART_SIZE,
    CIRCUIT_RAM_SIZE as _CIRCUIT_RAM_SIZE,
)


class _PartsTree(QTreeWidget):
    """QTreeWidget that carries part_id via MIME text when dragged."""

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return
        part = item.data(0, Qt.UserRole)
        if part is None:
            return
        mime = QMimeData()
        mime.setText(part["id"])
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(supported_actions)


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AKDev")
        self.resize(1280, 800)
        self._project_root: Path | None = None
        self._address_map: dict[int, int] = {}
        # Runtime program loaded into the virtual circuit (PATCH_CIRCUIT_WRITE_RUN_HELLO_V05).
        self._loaded_program: "dict | None" = None
        # Per-device Address Map overrides (PATCH_ADDRESS_MAP_EDITOR_V08); empty = auto.
        self._address_overrides: dict = {}
        # Program load target (PATCH_PROGRAM_TARGET_ROM_V08): "ram" (default, fully
        # compatible) or "rom". ROM target only takes effect when a ROM runtime with a
        # resolved base exists; otherwise Write Program errors (no silent RAM fallback).
        self._program_target: str = "ram"
        self._setup_log()            # must be first — others write to self._log
        self._setup_console()        # Console: program/run output (tabified with Log)
        self._setup_uart_console()   # UART Console panel (tabified with Log)
        self._setup_bus_trace()      # Bus Trace panel (tabified with Log)
        self._setup_memory_viewer()  # Memory Viewer panel (tabified with Log)
        self._setup_sim()            # creates self._sim_bus/ram/uart/cpu
        self._setup_canvas()         # creates self._canvas and self._editor_tabs
        self._setup_parts_lib()
        self._setup_properties()     # creates self._prop_panel, self._props_dock
        self._setup_register_view()  # Register View (tabified with Properties)
        self._setup_run_status()     # Run Status Panel (tabified with Register View)
        self._setup_port_detail()    # Port Detail Panel (tabified with Run Status)
        self._setup_address_map_editor()  # Address Map Editor (tabified with Port Detail)
        self._canvas.selection_changed.connect(self._on_canvas_selection)
        self._canvas.tab_open_requested.connect(self._on_open_tab)
        self._canvas.wire_selected.connect(self._on_wire_selected)
        self._canvas.wire_selection_cleared.connect(self._on_wire_selection_cleared)
        self._canvas.connections_changed.connect(self._update_port_detail)
        self._canvas.set_source_requested.connect(self._on_source_set)
        self._canvas.write_program_requested.connect(self.write_program)
        self._setup_menu()           # creates self._a_new/_a_open/_a_save/etc.
        self._setup_toolbar()        # reuses those actions
        self._update_register_view() # populate with initial CPU state
        self._update_run_status()    # populate Run Status Panel with initial state
        self._update_port_detail()   # populate Port Detail Panel with initial state
        self._arrange_initial_layout()  # lead with Log / Properties (Canvas主役)

    # ------------------------------------------------------------------ layout

    def _arrange_initial_layout(self):
        """v0.5 prototype initial display: lead with Log/Console and Properties.

        Debug panels (Register View / Memory / Bus Trace / UART) stay created
        and toggleable from the Debug ribbon tab, but are not raised to the
        front so the Canvas stays the focus.
        """
        self._log_dock.raise_()    # bottom tabs -> Log in front
        self._props_dock.raise_()  # right tabs  -> Properties in front
        # Patch 2 (H): Grid off at startup (Canvas default stays True; overridden here).
        self._canvas.set_grid_visible(False)
        self._a_grid.setChecked(False)
        # B3: make the canvas read as loaded — center on origin + ready cue.
        self._canvas.center_origin()
        self._log.append("Canvas ready")
        self.statusBar().showMessage("Canvas ready", 3000)

    # ---------------------------------------------------------------- hub entry

    def start_new_project(self):
        """Entry point used by the Hub to trigger the existing New flow."""
        self._new_project()

    def start_open_project(self):
        """Entry point used by the Hub to trigger the existing Open flow."""
        self._open_project()

    # ----------------------------------------------------------------- wiring

    def _on_mode_changed(self, mode: str):
        """Sync Wire Mode toggle + status bar with the canvas mode (PATCH_WIRING_V05)."""
        self._a_wire_mode.setChecked(mode == "wire")
        if mode == "wire":
            self.statusBar().showMessage(
                "Wire Mode: ON — パーツ右クリック「ここから接続を開始」→ 接続先で「ここに接続」"
                " ／ Esc・Cancel Wire で解除"
            )
            self._log.append("Wire Mode: ON")
        else:
            self.statusBar().clearMessage()

    def _cancel_wire_action(self):
        """Cancel Wire ribbon button — always return to design mode (PATCH_WIRING_V05)."""
        if self._canvas._mode == "wire":
            self._canvas.set_mode("design")
            self._log.append("Wire Mode canceled — design へ戻りました")
        else:
            self._log.append("Wire Mode は既に OFF です")

    # ------------------------------------------------------------------ sim setup

    def _setup_sim(self):
        self._sim_cycle: int        = 0   # init before Bus so cycle_fn lambda works
        self._pause_requested: bool = False
        self._make_sim()

    def _make_sim(self, plan: "dict | None" = None):
        """(Re)create the virtual circuit devices + runtime.

        Called once at startup (legacy fixed circuit) and again when a Canvas
        circuit is written. In **circuit mode** (a CircuitPlan with a CPU and a
        connected RAM + UART) the devices are built *from the plan* and used as the
        runtime's execution devices — the connected RAM/UART nodes are the ones that
        actually run (PATCH_PLAN_DRIVEN_DEVICES_V07). In **legacy mode** (no CPU on
        canvas / plan=None) the original fixed 256-byte circuit is kept unchanged.

        Memory map: UART stays at 0x0100. In circuit mode the RAM fills the whole
        64 KB address space with the UART as a memory-mapped I/O window inside it
        (RAM attached for 0x0000–0x00FF and 0x0108–0xFFFF), so code still starts at
        0x0000 and all addresses stay within the LDI imm16 range.

        PATCH_DEVICE_REGISTRY_REFACTOR_V08: the body is now device-spec/list driven
        (placed node -> device spec -> runtime device / Address Map), but the
        external behaviour is unchanged.
        """
        self._sim_bus = Bus(cycle_fn=lambda: self._sim_cycle)
        mode, layout, specs = self._resolve_device_specs(plan)
        self._build_runtime_devices(plan, mode, layout, specs)

    # ----------------------------------------- device registry (PATCH_DEVICE_REGISTRY_REFACTOR_V08)

    def _auto_device_specs(self, plan: "dict | None"):
        """Return ``(mode, layout, device_specs)`` from automatic placement only.

        The MemoryLayout (PATCH_CODE_REGION_MMIO_RELOCATION_V08) decides RAM/MMIO
        base+size; the default is the current behaviour (circuit_compat / legacy).
        circuit mode classifies the resolved CPU/RAM/UART nodes by part_id (so e.g.
        a ``mem.vram`` node is *not* treated as RAM). legacy mode is the fixed
        synthetic CPU + 256B RAM + UART circuit (no canvas dependency — this also
        runs at startup before the canvas exists). No per-device overrides applied.
        """
        circuit = bool(plan and plan.get("cpu") and plan.get("rams") and plan.get("uarts"))
        mode = "circuit" if circuit else "legacy"
        layout = get_memory_layout(mode)
        if not circuit:
            return mode, layout, assign_mmio_bases(legacy_device_specs(layout), layout=layout)
        # PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08: spec ALL resolved RAM/UART nodes (not
        # just the first); PATCH_INPUT_DEVICE_V08: Input nodes too. assign_mmio_bases
        # then auto-places MMIO windows in encounter order (UART=0x0100, Input=0x0110…).
        specs = [make_device_spec(plan["cpu"], self._part_of(plan["cpu"]), layout=layout)]
        for node_id in plan["rams"]:
            specs.append(make_device_spec(node_id, self._part_of(node_id), layout=layout))
        for node_id in plan["uarts"]:
            specs.append(make_device_spec(node_id, self._part_of(node_id), layout=layout))
        for node_id in plan.get("inputs", []):
            specs.append(make_device_spec(node_id, self._part_of(node_id), layout=layout))
        # PATCH_ROM_DEVICE_V08: ROM (read-only memory) nodes too. In circuit_compat
        # the ROM has no auto base (layout.rom_base is None) and is only placed once
        # an Address Map Editor override gives it a base/size; game16 auto-places it.
        for node_id in plan.get("roms", []):
            specs.append(make_device_spec(node_id, self._part_of(node_id), layout=layout))
        return mode, layout, assign_mmio_bases(specs, layout=layout)

    def _resolve_device_specs(self, plan: "dict | None"):
        """Auto specs + per-device Address Map overrides (PATCH_ADDRESS_MAP_EDITOR_V08).

        With no overrides this is identical to the automatic placement, so the
        default behaviour is unchanged.
        """
        mode, layout, specs = self._auto_device_specs(plan)
        specs = apply_address_overrides(specs, self._address_overrides)
        return mode, layout, specs

    def _part_of(self, node_id):
        node = self._canvas.get_node(node_id) if node_id else None
        return node.part() if node else None

    def _build_runtime_devices(self, plan, mode, layout, specs):
        """Instantiate runtime Parts from device specs and bind the runtime.

        Only ``runtime_backed`` kinds (cpu/ram/uart/input) are instantiated, and only
        the FIRST of each kind — their ``runtime_id`` (sim_cpu/sim_ram/sim_uart/
        sim_input) is kept stable for bus tracing, the signal overlay and the
        runtime's UART detection. A ``vram`` / extra-UART / extra-Input / extra-RAM
        spec is classified + (for MMIO) placed on the Address Map, but NOT turned
        into a runtime Part (full multi-device runtime is later). The CPU reset PC
        comes from the layout (PATCH_CODE_REGION_MMIO_RELOCATION_V08; default 0x0000).
        """
        self._sim_ram = self._sim_uart = self._sim_cpu = None
        self._sim_input = self._sim_rom = None
        self._sim_ram_node = self._sim_uart_node = self._sim_cpu_node = None
        self._sim_input_node = self._sim_rom_node = None
        # PATCH_PROGRAM_TARGET_ROM_V08: when the program target is ROM and a ROM
        # runtime base is resolved, the CPU resets to the ROM base so it fetches the
        # program from ROM. The ROM spec can appear after the CPU spec, so resolve the
        # base in a pre-pass. Otherwise the layout reset PC (default 0x0000) is kept,
        # which preserves the existing RAM-target behaviour exactly.
        cpu_reset_pc = layout.reset_pc
        if self._program_target == "rom":
            rom_base = next(
                (s["base"] for s in specs
                 if s.get("kind") == "rom" and s.get("runtime_backed")
                 and s.get("base") is not None),
                None,
            )
            if rom_base is not None:
                cpu_reset_pc = rom_base
        for spec in specs:
            if not spec.get("runtime_backed"):
                continue
            kind = spec["kind"]
            if kind == "ram" and self._sim_ram is None:
                self._sim_ram = RamPart("sim_ram", "RAM",
                                        size=spec["size"], base=spec["base"])
                self._sim_ram_node = spec["node_id"]
            elif kind == "rom" and self._sim_rom is None and spec.get("base") is not None:
                # Read-only memory; built only when it has a base (game16 auto / Editor
                # override). In circuit_compat with no override, ROM stays unplaced
                # (PATCH_ROM_DEVICE_V08). Program loading still targets RAM.
                self._sim_rom = RomPart("sim_rom", "ROM",
                                        size=spec["size"], base=spec["base"])
                self._sim_rom_node = spec["node_id"]
            elif kind == "uart" and self._sim_uart is None:
                self._sim_uart = UartPart("sim_uart", "UART", base=spec["base"])
                self._sim_uart_node = spec["node_id"]
            elif kind == "input" and self._sim_input is None:
                self._sim_input = InputPart("sim_input", "INPUT", base=spec["base"])
                self._sim_input_node = spec["node_id"]
            elif kind == "cpu" and self._sim_cpu is None:
                self._sim_cpu = AK32Part("sim_cpu", "AK32", self._sim_bus,
                                         reset_pc=cpu_reset_pc)
                self._sim_cpu_node = spec["node_id"]

        # Address Map from the addressable specs: the first RAM (memory container) +
        # all MMIO windows (UART/Input). 2nd+ RAM is NOT placed (16-bit space; warned
        # via multi_device_warnings). The map carves the RAM around every MMIO window.
        addr_specs, seen_ram, seen_rom = [], False, False
        for s in specs:
            if not s.get("addressable"):
                continue
            if s.get("base") is None:
                continue   # unplaced (e.g. circuit_compat ROM with no override)
            if s["kind"] == "ram":
                if seen_ram:
                    continue
                seen_ram = True
            if s["kind"] == "rom":
                if seen_rom:
                    continue
                seen_rom = True
            addr_specs.append(s)
        amap = build_address_map_from_devices(mode, addr_specs, layout=layout)

        parts_by_id = {}
        if self._sim_ram is not None:
            parts_by_id["sim_ram"] = self._sim_ram
        if self._sim_uart is not None:
            parts_by_id["sim_uart"] = self._sim_uart
        if self._sim_input is not None:
            parts_by_id["sim_input"] = self._sim_input
        if self._sim_rom is not None:
            parts_by_id["sim_rom"] = self._sim_rom
        for dev in amap["devices"]:
            part = parts_by_id.get(dev.get("device_id"))
            if part is None:
                continue   # extra MMIO windows are placed/diagnosed only (no Part)
            for lo, hi in dev["attach_ranges"]:
                self._sim_bus.attach(part, lo, hi - lo + 1)

        self._sim_bus.tracing = True      # enable bus tracing
        # Virtual circuit runtime — wraps the devices for stepped, traced execution.
        self._runtime = VirtualCircuitRuntime(
            self._sim_bus, self._sim_ram, self._sim_uart, self._sim_cpu
        )
        self._runtime.plan = plan
        self._runtime.address_map = amap   # PATCH_ADDRESS_MAP_V07
        # Diagnostics (warning only): unsupported multi-device configs (e.g. >1 RAM).
        for w in multi_device_warnings(specs):
            self._log.append(f"Address Map warning: {w['code']} — {w.get('message')}")

    def address_map(self) -> "dict | None":
        """Return the current Address Map (device layout on the bus)."""
        return self._runtime.address_map

    def set_input_keys(self, mask: int) -> None:
        """Set the runtime Input device's held-key bitmask (PATCH_INPUT_DEVICE_V08).

        No-op when no Input device is on the canvas. The CPU reads the keys with the
        existing ``LD`` instruction (Input is MMIO-mapped); no ``IN`` instruction.
        """
        if self._sim_input is not None:
            self._sim_input.set_keys(mask)
            self._refresh_run_panels()

    # ----------------------------------------- circuit resolve (PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05)

    def _resolve_circuit_plan(self) -> dict:
        """Resolve a CircuitPlan from the current Canvas topology."""
        nodes = [
            {"node_id": n.node_id(),
             "category": n.part().get("category", ""),
             "part_id":  n.part().get("id", ""),
             "name":     n.part().get("name", "")}
            for n in self._canvas.get_all_nodes()
        ]
        conns = [
            {"from_node": c["from"]["node_id"], "to_node": c["to"]["node_id"]}
            for c in self._canvas.export_canvas()["connections"]
        ]
        # PATCH_TARGET_CPU_SELECTION_V07: the selected node decides which CPU runs
        # when several CPUs are placed (single CPU ignores the selection).
        target = self._canvas.selected_node_id()
        return resolve_circuit(nodes, conns, target_cpu_id=target)

    def _circuit_guard(self, action: str) -> "dict | None":
        """Return the plan if execution is allowed, else None (and log the block).

        In *circuit mode* (any CPU on canvas) the circuit must be fully wired
        (CPU↔RAM, CPU↔UART). In *legacy mode* (no CPU placed) the fixed runtime
        is used and nothing is blocked, preserving existing non-canvas flows.
        """
        plan = self._resolve_circuit_plan()
        if plan["cpu_present"] and not plan["ok"]:
            self._log.append(f"{action} blocked — " + "; ".join(plan["issues"]))
            return None
        return plan

    def _bind_circuit_runtime(self, plan: dict) -> None:
        """Rebuild the virtual circuit runtime bound to a resolved CircuitPlan.

        Called by Write Program / Build (a load operation): fresh devices are
        created and the program is loaded immediately after. Run/Step never call
        this (they keep the loaded runtime).
        """
        self._make_sim(plan)
        self._sim_cycle = 0
        # PATCH_TARGET_CPU_SELECTION_V07: surface which CPU is the execution target.
        self._log.append(f"Target CPU: {plan.get('target_cpu', plan['cpu'])}")
        self._log.append(
            f"Circuit built: CPU={plan['cpu']} "
            f"RAM={plan['rams']} UART={plan['uarts']}"
        )
        self._log_address_map()

    def _log_address_map(self) -> None:
        """Emit the current Address Map summary (+ any overlap issues) to the Log."""
        amap = self._runtime.address_map
        if not amap:
            return
        for line in format_address_map_summary(amap):
            self._log.append(line)
        for issue in validate_address_map(amap):
            self._log.append(f"Address Map issue: {issue}")

    # ------------------------------------------------------------------ helpers

    def _act(self, text, shortcut=None):
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(lambda: self._log.append(f"Action: {text}"))
        return a

    # ------------------------------------------------------------------ setup

    def _setup_log(self):
        # Patch 2: "Log" = app operations / build results / status notifications.
        self._log_dock = QDockWidget("Log", self)
        self._log_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self._log_dock.setMinimumHeight(100)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Log output...")
        self._log_dock.setWidget(self._log)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._log_dock)

    def _setup_console(self):
        # Patch 2: "Console" = running program output (run state + UART text).
        self._console_dock = QDockWidget("Console", self)
        self._console_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self._console = QPlainTextEdit()
        self._console.setReadOnly(True)
        self._console.setPlaceholderText("Program output...")
        font = self._console.font()
        font.setFamily("Courier New")
        self._console.setFont(font)
        self._console_dock.setWidget(self._console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._console_dock)
        self.tabifyDockWidget(self._log_dock, self._console_dock)

    def _setup_uart_console(self):
        self._uart_console_dock = QDockWidget("UART Console", self)
        self._uart_console_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self._uart_console = QPlainTextEdit()
        self._uart_console.setReadOnly(True)
        self._uart_console.setPlaceholderText("UART output...")
        font = self._uart_console.font()
        font.setFamily("Courier New")
        self._uart_console.setFont(font)
        self._uart_console_dock.setWidget(self._uart_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._uart_console_dock)
        self.tabifyDockWidget(self._log_dock, self._uart_console_dock)

    def _setup_bus_trace(self):
        self._bus_trace_dock = QDockWidget("Bus Trace", self)
        self._bus_trace_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self._bus_trace = QPlainTextEdit()
        self._bus_trace.setReadOnly(True)
        self._bus_trace.setPlaceholderText("Bus read/write trace...")
        font = self._bus_trace.font()
        font.setFamily("Courier New")
        self._bus_trace.setFont(font)
        self._bus_trace_dock.setWidget(self._bus_trace)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._bus_trace_dock)
        self.tabifyDockWidget(self._log_dock, self._bus_trace_dock)

    def _setup_memory_viewer(self):
        self._mem_viewer = MemoryViewer(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._mem_viewer)
        self.tabifyDockWidget(self._log_dock, self._mem_viewer)

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
        self._parts_tree = _PartsTree()
        self._parts_tree.setHeaderHidden(True)
        self._parts_tree.setDragEnabled(True)

        cats, errors = load_parts()
        lib: dict = {}
        for cat_key, parts in cats.items():
            cat_item = QTreeWidgetItem(self._parts_tree, [cat_label(cat_key)])
            for p in parts:
                child = QTreeWidgetItem(cat_item, [p["name"]])
                child.setData(0, Qt.UserRole, p)
                lib[p["id"]] = p
        self._parts_tree.expandAll()
        self._parts_tree.itemDoubleClicked.connect(self._on_part_dbl_click)
        self._canvas.set_part_library(lib)

        for err in errors:
            self._log.append(err)

        dock.setWidget(self._parts_tree)
        self._parts_lib_dock = dock
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        # Patch 2 (D): hidden on startup so the Canvas leads; the Parts ribbon
        # tab toggles it back on. Drag & drop placement is unaffected.
        dock.hide()

    def _on_part_dbl_click(self, item, _col):
        part = item.data(0, Qt.UserRole)
        if part:
            self._canvas.add_part(part)

    def _open_parts_folder(self):
        """Ribbon 'Open Parts Folder' — open the parts/ directory in the OS file manager."""
        parts_dir = (Path(__file__).resolve().parent.parent / "parts")
        if not parts_dir.exists():
            self._log.append(f"Open Parts Folder: ディレクトリが見つかりません — {parts_dir.as_posix()}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(parts_dir)))
        self._log.append(f"Open Parts Folder: {parts_dir.as_posix()}")

    def _setup_properties(self):
        self._props_dock = QDockWidget("Properties", self)
        self._props_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._props_dock.setMinimumWidth(180)
        self._prop_panel = PropPanel()
        self._prop_panel.color_changed.connect(self._on_part_color_changed)
        self._prop_panel.wire_color_changed.connect(self._on_wire_color_changed)
        self._prop_panel.wire_width_changed.connect(self._on_wire_width_changed)
        self._prop_panel.wire_style_reset.connect(self._on_wire_style_reset)
        self._prop_panel.source_set_requested.connect(self._on_source_set)
        self._prop_panel.source_clear_requested.connect(self._on_source_clear)
        self._prop_panel.source_open_requested.connect(self._on_source_open)
        self._props_dock.setWidget(self._prop_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self._props_dock)

    def _on_part_color_changed(self, node_id: str, color: str):
        """PATCH_PART_VISUAL_V05: apply a Properties color pick to the node + save."""
        if self._canvas.set_node_color(node_id, color) and self._project_root is not None:
            self._persist_system()

    # ------------------------------------------------- wire style (PATCH_WIRE_STYLE_V05)

    def _on_wire_selected(self, conn: dict):
        self._prop_panel.show_wire(conn)
        self._update_port_detail()   # PATCH_PORT_DETAIL_V07

    def _on_wire_selection_cleared(self):
        self._prop_panel.show_none()
        self._update_port_detail()   # PATCH_PORT_DETAIL_V07

    def _on_wire_color_changed(self, conn_id: str, color: str):
        if self._canvas.set_connection_style(conn_id, color=color) and self._project_root is not None:
            self._persist_system()

    def _on_wire_width_changed(self, conn_id: str, width: float):
        if self._canvas.set_connection_style(conn_id, width=width) and self._project_root is not None:
            self._persist_system()

    def _on_wire_style_reset(self, conn_id: str):
        if self._canvas.reset_connection_style(conn_id) and self._project_root is not None:
            self._persist_system()

    # ----------------------------------------- program sources (PATCH_PART_PROGRAM_ASSIGN_V05)

    _SRC_FILTER = {
        "asm": "ASM (*.asm *.s);;All files (*)",
        "hdl": "HDL (*.v *.sv *.vhdl *.vh);;All files (*)",
        "rom": "ROM (*.bin *.hex *.rom);;All files (*)",
    }

    def _rel_to_root(self, path: str) -> str:
        """Return a project-root-relative posix path when possible, else absolute."""
        p = Path(path)
        if self._project_root is not None:
            try:
                return p.resolve().relative_to(self._project_root.resolve()).as_posix()
            except ValueError:
                pass  # outside the project — keep absolute (future: portability)
        return p.as_posix()

    def _loaded_for(self, node_id: str) -> "dict | None":
        """Return the loaded_program dict if it targets node_id, else None."""
        lp = self._loaded_program
        if lp and lp.get("target_node_id") == node_id:
            return lp
        return None

    def _refresh_node_properties(self, node_id: str):
        node = self._canvas.get_node(node_id)
        if node is not None:
            self._prop_panel.show_part(
                node.part(), node_id, self._canvas.node_sources(node_id),
                self._loaded_for(node_id),
            )

    def _on_source_set(self, node_id: str, source_type: str):
        start = str(self._project_root) if self._project_root is not None else ""
        path, _ = QFileDialog.getOpenFileName(
            self, f"Set {source_type.upper()} Source", start,
            self._SRC_FILTER.get(source_type, "All files (*)"),
        )
        if not path:
            return
        rel = self._rel_to_root(path)
        if self._canvas.set_node_source(node_id, source_type, rel):
            self._log.append(f"Source set: [{node_id}] {source_type} = {rel}")
            if self._project_root is not None:
                self._persist_system()
            self._refresh_node_properties(node_id)

    def _on_source_clear(self, node_id: str, source_type: str):
        if self._canvas.clear_node_source(node_id, source_type):
            self._log.append(f"Source cleared: [{node_id}] {source_type}")
            if self._project_root is not None:
                self._persist_system()
            self._refresh_node_properties(node_id)

    def _on_source_open(self, node_id: str, source_type: str):
        src = self._canvas.node_source(node_id, source_type)
        if not src:
            self._log.append(f"No {source_type.upper()} source assigned for [{node_id}]")
            return
        node = self._canvas.get_node(node_id)
        if node is None:
            return
        ext = {"asm": "asm", "hdl": "v"}.get(source_type, source_type)
        self._on_open_tab(node.part(), node_id, ext)

    def _resolve_source_path(self, rel: "str | None") -> "Path | None":
        """Resolve a source path against the project root; None if missing/absent."""
        if not rel:
            return None
        p = Path(rel)
        path = p if p.is_absolute() else (
            (self._project_root / rel) if self._project_root is not None else p
        )
        if not path.exists():
            self._log.append(f"Source not found: {path.as_posix()}")
            return None
        return path

    def _resolve_assigned_asm_path(self) -> "Path | None":
        """Pick an assigned asm by priority (selected > CPU > any) and resolve it."""
        rel = self._canvas.resolve_program_source("asm")
        return self._resolve_source_path(rel)

    def _circuit_asm_source(self, plan: dict) -> "tuple | None":
        """Return (target_node_id, rel_path) for the target CPU's asm, else None.

        Circuit mode never falls back to another CPU's source
        (PATCH_TARGET_CPU_SELECTION_V07): only the resolved target CPU's
        ``sources.asm`` is used, so a multi-CPU canvas can't accidentally run a
        non-selected CPU's program.
        """
        target = plan.get("target_cpu") or plan.get("cpu")
        rel = self._canvas.node_source(target, "asm")
        if not rel:
            return None
        return (target, rel)

    def _setup_register_view(self):
        dock = QDockWidget("Register View", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setMinimumWidth(200)

        _ROWS = ["pc", "cycle", "halted"] + [f"r{i}" for i in range(16)]
        self._reg_table = QTableWidget(len(_ROWS), 2)
        self._reg_table.setHorizontalHeaderLabels(["Register", "Value"])
        self._reg_table.verticalHeader().setVisible(False)
        self._reg_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._reg_table.horizontalHeader().setStretchLastSection(True)
        for row, name in enumerate(_ROWS):
            self._reg_table.setItem(row, 0, QTableWidgetItem(name))
            self._reg_table.setItem(row, 1, QTableWidgetItem("---"))

        dock.setWidget(self._reg_table)
        self._reg_view_dock = dock
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.tabifyDockWidget(self._props_dock, dock)

    def _setup_run_status(self):
        """Run Status Panel — read-only execution summary (PATCH_RUN_STATUS_PANEL_V07)."""
        self._run_status = RunStatusPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self._run_status)
        self.tabifyDockWidget(self._reg_view_dock, self._run_status)

    def _setup_port_detail(self):
        """Port Detail Panel — read-only ports/connections view (PATCH_PORT_DETAIL_V07)."""
        self._port_detail = PortDetailPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self._port_detail)
        self.tabifyDockWidget(self._run_status, self._port_detail)

    def _setup_address_map_editor(self):
        """Address Map Editor — view + per-device base/size override (PATCH_ADDRESS_MAP_EDITOR_V08)."""
        self._address_map_editor = AddressMapEditor(self, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self._address_map_editor)
        self.tabifyDockWidget(self._port_detail, self._address_map_editor)

    # ----------------------------------------- address map editor (PATCH_ADDRESS_MAP_EDITOR_V08)

    def address_editor_data(self):
        """Return ``(auto_addressable_specs, overrides_copy, layout)`` for the editor.

        Auto specs = device specs BEFORE per-device overrides, so the editor shows the
        automatic placement and the current manual overrides separately.
        """
        _mode, layout, specs = self._auto_device_specs(self._resolve_circuit_plan())
        addr = [s for s in specs if s.get("addressable")]
        return addr, dict(self._address_overrides), layout

    def validate_address_map_overrides(self, overrides: dict) -> list:
        """Validate proposed overrides against the current auto specs (read-only)."""
        _mode, layout, specs = self._auto_device_specs(self._resolve_circuit_plan())
        addr = [s for s in specs if s.get("addressable")]
        return validate_address_overrides(addr, overrides, layout=layout)

    def apply_address_map_overrides(self, overrides: dict) -> None:
        """Set overrides, rebuild the runtime/Address Map, refresh panels (+ persist)."""
        self._address_overrides = dict(overrides or {})
        self._rebuild_devices()
        self._log.append(
            f"Address Map overrides applied: {len(self._address_overrides)} device(s)"
        )
        if self._project_root is not None:
            self._persist_system()

    def reset_address_map_overrides(self) -> None:
        """Clear all overrides (back to automatic layout) and rebuild."""
        self._address_overrides = {}
        self._rebuild_devices()
        self._log.append("Address Map overrides reset to auto")
        if self._project_root is not None:
            self._persist_system()

    def _rebuild_devices(self) -> None:
        """Rebuild the device runtime + Address Map from the current canvas/overrides.

        Note: like Write/Build this re-creates the runtime (RAM is cleared), so a
        loaded program must be re-written after an address-map change.
        """
        self._make_sim(self._resolve_circuit_plan())
        self._sim_cycle = 0
        self._refresh_run_panels()
        self._update_port_detail()

    # ----------------------------------------- program target (PATCH_PROGRAM_TARGET_ROM_V08)

    @staticmethod
    def _normalize_program_target(value) -> str:
        """Coerce *value* to a valid target. Unknown / missing -> ``"ram"`` (default)."""
        return value if value in ("ram", "rom") else "ram"

    def program_target(self) -> str:
        """Return the current program load target (``"ram"`` or ``"rom"``)."""
        return self._program_target

    def set_program_target(self, target: str) -> None:
        """Set the program load target and persist it (ROM/RAM Write Program switch).

        Invalid values fall back to ``"ram"`` (logged). The new target affects the
        CPU reset PC and the load destination on the next Write Program, which
        rebuilds the runtime; the status panel is refreshed immediately.
        """
        norm = self._normalize_program_target(target)
        if norm != target:
            self._log.append(
                f"Program Target: 不正値 '{target}' -> RAM にフォールバックしました"
            )
        self._program_target = norm
        self._log.append(f"Program Target: {self._program_target_status()}")
        self._update_run_status()
        if self._project_root is not None:
            self._persist_system()

    def _rom_runtime_ready(self) -> bool:
        """True if a ROM runtime with a resolved base exists (ROM target viable)."""
        return self._sim_rom is not None and self._sim_rom.base is not None

    def _program_target_status(self) -> str:
        """Human-readable current target (e.g. ``"RAM"`` / ``"ROM @0x0000"``)."""
        if self._program_target != "rom":
            return "RAM"
        if self._rom_runtime_ready():
            return f"ROM @0x{self._sim_rom.base:04x}"
        return "ROM (unplaced)"

    def _load_program_to_ram(self, binary: bytes, source_name: str = "") -> None:
        """Load *binary* into RAM via the runtime (existing default behaviour)."""
        self._runtime.load_program(binary, source_name=source_name)

    def _load_program_to_rom(self, binary: bytes, source_name: str = "") -> bool:
        """Load *binary* into ROM via ``RomPart.load_bytes`` (IDE loader, not the bus).

        Validates that a ROM runtime exists, is placed, the Address Map has no overlap
        errors, and the program fits. On any failure the program is NOT loaded and
        NOT written to RAM (no silent fallback); the error is logged and False is
        returned. On success the working RAM is cleared and the CPU/UART/trace are
        reset (the CPU's reset PC is already the ROM base from the runtime rebuild).
        """
        rom = self._sim_rom
        if rom is None:
            self._log.append(
                "Write Program: ROM target ですが ROM runtime がありません"
                "（ROM を配置するか RAM target にしてください）"
            )
            return False
        if rom.base is None or rom.size is None:
            self._log.append(
                "Write Program: ROM target ですが ROM の base/size が未確定です"
                "（Address Map Editor で配置してください）"
            )
            return False
        amap = self._runtime.address_map
        issues = validate_address_map(amap) if amap else []
        if issues:
            self._log.append(
                "Write Program: ROM target ですが Address Map に問題があります: "
                + "; ".join(str(i) for i in issues)
            )
            return False
        if len(binary) > rom.size:
            self._log.append(
                f"Write Program: ROM target ですが program ({len(binary)} B) が "
                f"ROM size (0x{rom.size:x} B) を超えています"
            )
            return False
        try:
            rom.load_bytes(binary)
        except ValueError as exc:
            self._log.append(f"Write Program: ROM load failed: {exc}")
            return False
        # ROM holds the program; clear the working RAM and reset CPU/UART/trace. The
        # runtime stays valid and is marked loaded so Step/Run can proceed.
        if self._runtime.ram is not None:
            self._runtime.ram.reset()
        self._runtime.reset()
        self._runtime.loaded = True
        self._runtime.loaded_program = {
            "source_name":    source_name,
            "target_node_id": None,
            "size":           len(binary),
        }
        return True

    # ----------------------------------------- port detail (PATCH_PORT_DETAIL_V07)

    def _collect_port_detail(self) -> dict:
        """Build a Port Detail info dict for the current selection (wire > node > none)."""
        try:
            conn_id = self._canvas.selected_conn_id()
            if conn_id is not None:
                return build_wire_info(self._canvas, conn_id)
            node_id = self._canvas.selected_node_id()
            if node_id is not None:
                return build_node_info(self._canvas, node_id)
        except Exception:
            return {"selection": "none"}
        return {"selection": "none"}

    def _update_port_detail(self) -> None:
        """Refresh the Port Detail Panel from the current selection."""
        self._port_detail.update_detail(self._collect_port_detail())

    # ------------------------------------------- run status (PATCH_RUN_STATUS_PANEL_V07)

    def _collect_run_status(self) -> dict:
        """Build a snapshot dict of the current execution state from existing state.

        Reads the resolved CircuitPlan, the runtime, the sim devices and the
        Address Map — it adds no new state. Safe in legacy / ambiguous / unwired /
        unloaded situations (every lookup is defensive).
        """
        try:
            plan = self._resolve_circuit_plan()
        except Exception:
            plan = {"cpu_present": False, "target_cpu": None,
                    "rams": [], "uarts": [], "issues": []}
        mode = "circuit" if plan.get("cpu_present") else "legacy"

        # Device description depends on the mode.
        if mode == "circuit":
            rams  = plan.get("rams") or []
            uarts = plan.get("uarts") or []
            ram_desc  = ", ".join(rams) if rams else "(none connected)"
            uart_desc = ", ".join(uarts) if uarts else "(none connected)"
        else:
            ram_desc  = f"sim_ram ({self._sim_ram.size}B)"
            uart_desc = f"sim_uart (0x{_SIM_UART_BASE:04x})"

        # Combine the win-level loaded_program with the runtime's loaded_program.
        lp    = self._loaded_program or {}
        rt_lp = self._runtime.loaded_program or {}
        program = None
        if self._runtime.loaded or lp or rt_lp:
            program = {
                "source_type":    lp.get("source_type"),
                "path":           lp.get("path") or rt_lp.get("source_name"),
                "target_node_id": lp.get("target_node_id") or rt_lp.get("target_node_id"),
                "status":         lp.get("status"),
                "size":           rt_lp.get("size"),
            }

        amap = self._runtime.address_map or self.address_map()
        amap_lines  = format_address_map_summary(amap) if amap else []
        amap_issues = validate_address_map(amap) if amap else []

        return {
            "mode":        mode,
            "program_target": self._program_target_status(),
            "target_cpu":  plan.get("target_cpu"),
            "ram_desc":    ram_desc,
            "uart_desc":   uart_desc,
            "issues":      plan.get("issues") or [],
            "program":     program,
            "pc":          self._sim_cpu.pc(),
            "cycle":       self._sim_cycle,
            "halted":      self._sim_cpu.halted(),
            "step_count":  self._runtime.step_count,
            "last_trace":  self._runtime.last_trace,
            "address_map_lines":  amap_lines,
            "address_map_issues": amap_issues,
            "uart_out":    self._sim_uart.output_text(),
        }

    def _update_run_status(self) -> None:
        """Refresh the Run Status Panel from the current execution state."""
        self._run_status.update_status(self._collect_run_status())

    def _on_canvas_selection(self, nodes: list):
        self._update_port_detail()   # PATCH_PORT_DETAIL_V07: reflect new selection
        if not nodes:
            # Keep the Wire view if a wire is selected (node selection was cleared
            # so the wire could take over Properties — PATCH_WIRE_STYLE_V05).
            if self._canvas.selected_conn_id() is not None:
                return
            self._prop_panel.show_none()
        elif len(nodes) == 1:
            n = nodes[0]
            self._prop_panel.show_part(
                n.part(), n.node_id(), self._canvas.node_sources(n.node_id()),
                self._loaded_for(n.node_id()),
            )
        else:
            self._prop_panel.show_multi(len(nodes))

    def _on_open_tab(self, part: dict, node_id: str, ext: str):
        if self._project_root is None:
            self._log.append("プロジェクトを先に開いてください")
            return

        node = self._canvas.get_node(node_id)
        source_key = "asm" if ext == "asm" else "hdl"
        sources = node.sources() if node else {"asm": None, "hdl": None}
        source_rel = sources.get(source_key)

        if source_rel is None:
            default_name = f"main.{ext}"
            name, ok = QInputDialog.getText(
                self, "ファイル名",
                f"ソースファイル名を入力してください (例: {default_name}):",
                text=default_name,
            )
            if not ok:
                return
            name = name.strip()
            if not name.endswith(f".{ext}"):
                name = f"{name}.{ext}"

            err = validate_source_name(name, ext)
            if err:
                self._log.append(f"ファイル名エラー: {err}")
                return

            # Confirm the resolved path stays inside project_root/src/
            try:
                resolved = (self._project_root / "src" / name).resolve()
                src_dir  = (self._project_root / "src").resolve()
                resolved.relative_to(src_dir)
            except ValueError:
                self._log.append("ファイル名エラー: src/ 外への保存はできません")
                return

            if (self._project_root / "src" / name).exists():
                self._log.append(
                    f"同名ファイルが既に存在します: {name} — 別の名前を入力してください"
                )
                return

            source_rel = f"src/{name}"
            if node:
                node.set_source(source_key, source_rel)
            self._persist_system()

        source_name = Path(source_rel).name
        tab_name = self._editor_tabs.open_tab(part, node_id, ext, source_name)
        if tab_name:
            self._log.append(f"Opened tab: {tab_name}")

    def _part_library(self) -> dict:
        """Return {part_id: part_dict} for all loaded parts."""
        cats, _ = load_parts()
        return {p["id"]: p for parts in cats.values() for p in parts}

    def _ensure_project_root(self) -> "Path | None":
        """Return the current project root, or None if not set."""
        return self._project_root

    def _new_project(self):
        parent = QFileDialog.getExistingDirectory(self, "New Project — 保存先フォルダを選択")
        if not parent:
            return
        name, ok = QInputDialog.getText(self, "New Project", "プロジェクト名を入力してください:")
        if not ok or not name.strip():
            return
        name = name.strip()
        root = Path(parent) / name
        try:
            create_project(root, name)
        except FileExistsError:
            self._log.append(f"New Project: フォルダが既に存在します — {root.as_posix()}")
            return
        self._project_root = root
        self._editor_tabs.close_all_tabs()
        self._editor_tabs.set_project_root(root)
        self._canvas.import_parts([], {})
        self._address_overrides = {}        # PATCH_ADDRESS_MAP_EDITOR_V08
        self._program_target = "ram"        # PATCH_PROGRAM_TARGET_ROM_V08 (new = RAM)
        self._address_map_editor.refresh()
        self._uart_console.clear()
        self._bus_trace.clear()
        self._log.append(f"New project: {root.as_posix()}")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project — project.json を選択", "",
            "AKDev Project (project.json);;JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return
        root = Path(path).parent
        try:
            project, system = load_project(root)
        except Exception as exc:
            self._log.append(f"Open failed: {exc}")
            return
        self._canvas.import_parts(system.get("parts", []), self._part_library())
        # PATCH_ADDRESS_MAP_EDITOR_V08: restore overrides (absent in old projects = {}).
        ov = system.get("address_map_overrides")
        self._address_overrides = dict(ov) if isinstance(ov, dict) else {}
        # PATCH_PROGRAM_TARGET_ROM_V08: restore program target (absent/invalid = RAM).
        self._program_target = self._normalize_program_target(
            system.get("program_target")
        )
        self._project_root = root
        self._editor_tabs.set_project_root(root)
        self._address_map_editor.refresh()
        self._log.append(
            f"Opened project: {root.as_posix()}  [{project.get('name', '?')}]"
        )

    def _persist_system(self):
        """Write current canvas state (including sources) to system.json."""
        root = self._project_root
        if root is None:
            return
        try:
            _, system = load_project(root)
        except Exception:
            system = {"chips": [], "parts": [], "links": [], "memory_map": []}
        system["parts"] = self._canvas.export_parts()
        # PATCH_ADDRESS_MAP_EDITOR_V08: persist per-device Address Map overrides.
        system["address_map_overrides"] = dict(self._address_overrides)
        # PATCH_PROGRAM_TARGET_ROM_V08: persist program load target (default "ram").
        system["program_target"] = self._program_target
        save_system(root, system)

    def _save_project(self):
        root = self._project_root
        if root is None:
            self._log.append("Save: New Project / Open Project / Save As を先に行ってください")
            return
        self._persist_system()
        tab_path = self._editor_tabs.save_current()
        if tab_path:
            self._log.append(f"Saved: {tab_path}")
        self._log.append(f"Saved project: {root.as_posix()}")

    def _save_project_as(self):
        parent = QFileDialog.getExistingDirectory(self, "Save As — 保存先フォルダを選択")
        if not parent:
            return
        name, ok = QInputDialog.getText(self, "Save Project As", "新しいプロジェクト名を入力してください:")
        if not ok or not name.strip():
            return
        name = name.strip()
        new_root = Path(parent) / name
        try:
            create_project(new_root, name)
        except FileExistsError:
            self._log.append(f"Save As: フォルダが既に存在します — {new_root.as_posix()}")
            return
        self._project_root = new_root
        self._editor_tabs.set_project_root(new_root)
        self._persist_system()
        tab_path = self._editor_tabs.save_current()
        if tab_path:
            self._log.append(f"Saved: {tab_path}")
        self._log.append(f"Saved project as: {new_root.as_posix()}")

    def _build(self):
        root = self._project_root
        # PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05: in circuit mode, gate on connectivity
        # and bind the runtime to the resolved circuit before loading.
        plan = self._circuit_guard("Build")
        if plan is None:
            return
        # PATCH_TARGET_CPU_SELECTION_V07: in circuit mode build the target CPU's
        # asm only (no fallback to another CPU / selected non-CPU node), so Build
        # uses the same target as Write/Run/Step.
        if plan["cpu_present"]:
            self._bind_circuit_runtime(plan)
            if root is None:
                self._log.append("Build: New Project / Open Project を先に行ってください")
                return
            resolved = self._circuit_asm_source(plan)
            if resolved is None:
                self._log.append("No ASM source assigned to target CPU")
                return
            asm_path = self._resolve_source_path(resolved[1])
            if asm_path is None:
                return
            try:
                text = asm_path.read_text(encoding="utf-8")
            except OSError as exc:
                self._log.append(f"Build: cannot read assigned asm: {exc}")
                return
            self._log.append(f"Build: using assigned asm {asm_path.as_posix()}")
            self._assemble_and_load(text, asm_path.name, root)
            return
        # Legacy mode (no CPU on canvas): prefer an asm assigned to a part
        # (PATCH_PART_PROGRAM_ASSIGN_V05; priority selected > CPU > any), else fall
        # back to the editor-tab build so the existing flow / hello.asm is unchanged.
        if root is not None:
            asm_path = self._resolve_assigned_asm_path()
            if asm_path is not None:
                try:
                    text = asm_path.read_text(encoding="utf-8")
                except OSError as exc:
                    self._log.append(f"Build: cannot read assigned asm: {exc}")
                    return
                self._log.append(f"Build: using assigned asm {asm_path.as_posix()}")
                self._assemble_and_load(text, asm_path.name, root)
                return

        tab = self._editor_tabs.current_tab_info()
        if tab is None or tab.ext != "asm":
            self._log.append("Build: current tab is not an asm file")
            return
        if root is None:
            self._log.append("Build: New Project / Open Project を先に行ってください")
            return
        self._assemble_and_load(tab.text, tab.source_name, root)

    def _assemble_and_load(self, text: str, source_name: str, root: "Path"):
        """Assemble asm text, write the .bin, and load it into simulator RAM.

        Shared by the editor-tab build and the assigned-part-source build
        (PATCH_PART_PROGRAM_ASSIGN_V05).
        """
        # Resolve build type from target.json (falls back to AK32 Baremetal default).
        try:
            target_cfg = load_target(root)
        except Exception as exc:
            self._log.append(f"Build: failed to read target.json: {exc}")
            return False
        build_cfg  = target_cfg.get("build", {})
        build_type = build_cfg.get("type", "internal_assembler")

        if build_type == "external_command":
            self._log.append("Build: external_command is not implemented yet")
            return False
        if build_type != "internal_assembler":
            self._log.append(f"Build: unsupported build type: {build_type}")
            return False

        try:
            binary, address_map = assemble_ex(text)
        except AsmError as exc:
            self._log.append(f"Build FAILED: {exc}")
            self._address_map = {}
            self._editor_tabs.clear_highlight()
            return False

        out_dir = root / "build" / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        bin_name = Path(source_name).stem + ".bin"
        out_path = out_dir / bin_name
        out_path.write_bytes(binary)
        self._log.append(
            f"Build succeeded: {out_path.as_posix()}  ({len(binary)} bytes)"
        )
        # Load binary into the virtual circuit via the selected program target. This
        # also marks the runtime as loaded so Step/Run can gate on it
        # (PATCH_VIRTUAL_CPU_STEP_TRACE_V05). RAM target is the default and unchanged;
        # ROM target loads via RomPart.load_bytes and errors instead of falling back to
        # RAM on failure (PATCH_PROGRAM_TARGET_ROM_V08).
        if self._program_target == "rom":
            if not self._load_program_to_rom(binary, source_name=source_name):
                self._address_map = {}
                self._editor_tabs.clear_highlight()
                return False
            dest = f"ROM @0x{self._sim_rom.base:04x}"
        else:
            self._load_program_to_ram(binary, source_name=source_name)
            dest = "RAM"
        self._sim_cycle = 0
        self._pause_requested = False
        self._log.append(f"Loaded binary to {dest}: {len(binary)} bytes")
        self._console.clear()
        self._console.appendPlainText(f"[build] loaded {len(binary)} bytes — ready")
        self._address_map = address_map
        self._update_uart_console()
        self._update_register_view()
        self._update_bus_trace()
        self._update_memory_viewer()
        self._editor_tabs.clear_highlight()
        self._canvas.clear_signal_overlay()
        self._update_run_status()
        return True

    # ------------------------------------- write program to circuit (PATCH_CIRCUIT_WRITE_RUN_HELLO_V05)

    def write_program(self, prefer_node_id: "str | None" = None) -> bool:
        """Assemble the assigned ASM and load it into the virtual circuit (RAM/CPU).

        "Write" here means loading into AKDev's virtual CPU/RAM — NOT an FPGA
        flash. Source is resolved by priority (selected > CPU > any assigned),
        not a fixed file. Returns True on success.
        """
        root = self._project_root
        if root is None:
            self._log.append("Write Program: New Project / Open Project を先に行ってください")
            return False
        # PATCH_VIRTUAL_CIRCUIT_RUNTIME_V05: in circuit mode the circuit must be
        # fully wired (CPU↔RAM, CPU↔UART) and the program is written to the
        # connected RAM of the resolved CPU.
        plan = self._circuit_guard("Write Program")
        if plan is None:
            return False
        if plan["cpu_present"]:
            self._bind_circuit_runtime(plan)
            # PATCH_TARGET_CPU_SELECTION_V07: write to the target CPU only — no
            # fallback to another CPU's source.
            resolved = self._circuit_asm_source(plan)
            if resolved is None:
                self._log.append("No ASM source assigned to target CPU")
                return False
        else:
            resolved = self._canvas.resolve_program_node("asm", prefer_node_id)
            if resolved is None:
                self._log.append("No ASM source assigned")
                return False
        node_id, rel = resolved
        path = self._resolve_source_path(rel)
        if path is None:
            self._log.append(f"Program source not found: {rel}")
            return False
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._log.append(f"Write Program: cannot read source: {exc}")
            return False
        if not self._assemble_and_load(text, path.name, root):
            self._log.append(f"Assemble failed: {rel}")
            self._loaded_program = None
            return False
        self._loaded_program = {
            "source_type":    "asm",
            "path":           rel,
            "target_node_id": node_id,
            "status":         "loaded",
        }
        # Record the target node on the runtime's loaded_program too (set by
        # load_program with target_node_id=None during _assemble_and_load).
        if self._runtime.loaded_program is not None:
            self._runtime.loaded_program["target_node_id"] = node_id
        self._log.append(f"Program written to circuit: {node_id} <- {rel}")
        self._refresh_node_properties(node_id)
        self._update_run_status()
        return True

    def loaded_program(self) -> "dict | None":
        return self._loaded_program

    # ------------------------------------------------------------------ run controls

    def _update_uart_console(self) -> None:
        """Refresh the UART Console widget from the current UART output."""
        self._uart_console.setPlainText(self._sim_uart.output_text())

    def _update_register_view(self) -> None:
        """Refresh the Register View table from the current CPU state."""
        regs   = self._sim_cpu.regs()
        pc     = self._sim_cpu.pc()
        halted = self._sim_cpu.halted()
        self._reg_table.item(0, 1).setText(f"0x{pc:04x}")
        self._reg_table.item(1, 1).setText(str(self._sim_cycle))
        self._reg_table.item(2, 1).setText("HALTED" if halted else "running")
        for i, val in enumerate(regs):
            self._reg_table.item(3 + i, 1).setText(f"0x{val:08x}")

    def _update_bus_trace(self) -> None:
        """Refresh the Bus Trace panel from accumulated trace entries."""
        self._bus_trace.setPlainText("\n".join(self._sim_bus.get_trace()))

    def _update_pc_highlight(self) -> None:
        """Update editor PC-line highlight from the current CPU program counter."""
        pc = self._sim_cpu.pc()
        ln = self._address_map.get(pc)
        if ln is not None:
            self._editor_tabs.highlight_line(ln)
        else:
            self._editor_tabs.clear_highlight()

    def _update_memory_viewer(self) -> None:
        """Refresh the Memory Viewer from simulator RAM."""
        try:
            self._mem_viewer.update_from_ram(self._sim_ram)
        except Exception:
            pass

    def _update_signal_overlay(self) -> None:
        """Refresh canvas signal overlay from the most recent bus transactions."""
        self._canvas.update_signal_overlay(self._sim_bus.last_transactions)

    def _has_program(self) -> bool:
        """True if a program has been loaded into the virtual circuit.

        Accepts both the runtime loader and the legacy direct-RAM-load path
        (used by some tests): a non-zero RAM image counts as loaded.
        """
        return self._runtime.loaded or any(self._sim_ram.dump())

    def _refresh_run_panels(self) -> None:
        """Update every execution-related panel after a Step/Run/Reset."""
        self._update_uart_console()
        self._update_register_view()
        self._update_bus_trace()
        self._update_memory_viewer()
        self._update_pc_highlight()
        self._update_signal_overlay()
        self._update_run_status()

    def _log_step_trace(self, trace: dict) -> None:
        """Emit a detailed one-instruction trace to the Log (UI trace 導線)."""
        self._log.append(
            f"[STEP {trace['step']:04d}] "
            f"PC 0x{trace['pc_before']:04x} -> 0x{trace['pc_after']:04x} "
            f"| {trace['instruction']}"
        )
        for name, (before, after) in trace["register_changes"].items():
            self._log.append(f"  REG {name}: {before} -> {after}")
        for m in trace["memory"]:
            arrow = "<-" if m["type"] == "write" else "->"
            verb  = "WRITE" if m["type"] == "write" else "READ"
            self._log.append(f"  MEM {verb} {m['addr']} {arrow} {m['value']}")
        for io in trace["io"]:
            arrow = "<-" if io["type"] == "write" else "->"
            verb  = "WRITE" if io["type"] == "write" else "READ"
            self._log.append(
                f"  IO {verb} {io['addr']} {arrow} {io['value']} ({io['device']})"
            )
        if trace["uart"]:
            self._log.append(f"  UART {trace['uart']!r}")
        if trace["error"]:
            self._log.append(f"  ERROR {trace['error']}")

    def _do_reset(self):
        """Reset CPU and UART (RAM keeps the loaded binary)."""
        self._runtime.reset()
        self._sim_cycle = 0
        self._pause_requested = False
        self._log.append(
            f"Reset: pc={self._sim_cpu.pc():#06x}  halted={self._sim_cpu.halted()}"
        )
        self._console.clear()
        self._update_uart_console()
        self._update_register_view()
        self._update_bus_trace()
        self._update_memory_viewer()
        self._editor_tabs.clear_highlight()
        self._canvas.clear_signal_overlay()
        self._update_run_status()

    def _do_step(self):
        """Execute one instruction on the virtual CPU and trace it."""
        if self._circuit_guard("Step") is None:
            return
        if not self._has_program():
            self._log.append("No program loaded. Use Write Program first.")
            return
        if self._sim_cpu.halted():
            self._log.append("CPU is halted")
            return
        trace = self._runtime.step()
        self._sim_cycle = self._runtime.step_count
        self._log_step_trace(trace)
        if trace["uart"]:
            self._console.insertPlainText(trace["uart"])
        self._refresh_run_panels()

    def _do_run(self):
        """Run = repeated Step, up to 1000 instructions or until halted."""
        if self._circuit_guard("Run") is None:
            return
        if not self._has_program():
            self._log.append("No program loaded. Use Write Program first.")
            return
        if self._sim_cpu.halted():
            self._log.append("Run: CPU is halted — Reset to restart")
            return
        self._pause_requested = False
        self._log.append("Run started")
        # Show the Address Map at run time for circuit-mode runs (PATCH_ADDRESS_MAP_V07).
        # Legacy runs keep their original log output unchanged.
        amap = self._runtime.address_map
        if amap and amap.get("mode") == "circuit":
            self._log_address_map()
        self._console.appendPlainText("[run] started\n")
        traces: list[dict] = []
        halted = False
        for _ in range(1000):
            if self._pause_requested:
                self._sim_cycle = self._runtime.step_count
                self._log.append(
                    f"Run paused at cycle {self._sim_cycle}"
                    f"  pc={self._sim_cpu.pc():#06x}"
                )
                self._refresh_run_panels()
                return
            trace = self._runtime.step()
            traces.append(trace)
            if trace["uart"]:
                self._console.insertPlainText(trace["uart"])
            if trace["halted"]:
                halted = True
                break
        self._sim_cycle = self._runtime.step_count
        uart_after = self._sim_uart.output_text()
        # Summary only (detailed per-step traces are kept in runtime.trace_history).
        self._log.append(
            f'Run finished: steps={len(traces)}, halted={halted}, uart="{uart_after}"'
        )
        if halted:
            self._console.appendPlainText(f"\n[run] HALTED at cycle {self._sim_cycle}")
        else:
            self._log.append(
                f"Run stopped (1000 cycle limit)  pc={self._sim_cpu.pc():#06x}"
            )
            self._console.appendPlainText("\n[run] stopped (1000 cycle limit)")
        self._refresh_run_panels()

    def _do_pause(self):
        """Request pause of the running simulation."""
        self._pause_requested = True
        self._log.append("Pause requested")

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

        self._a_save_as = QAction("Save Project As...", self)
        self._a_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._a_save_as.triggered.connect(self._save_project_as)

        fm = mb.addMenu("File")
        fm.addAction(self._a_new)
        fm.addAction(self._a_open)
        fm.addSeparator()
        fm.addAction(self._a_save)
        fm.addAction(self._a_save_as)
        fm.addSeparator()
        fm.addAction(self._act("Exit", "Ctrl+Q"))

        # Build / Run / View actions — no menus; shortcuts active via window
        self._a_build = QAction("Build", self)
        self._a_build.setShortcut(QKeySequence("F5"))
        self._a_build.triggered.connect(self._build)

        self._a_reset = QAction("Reset", self)
        self._a_reset.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self._a_reset.triggered.connect(self._do_reset)

        self._a_step = QAction("Step", self)
        self._a_step.setShortcut(QKeySequence("F10"))
        self._a_step.triggered.connect(self._do_step)

        self._a_write_program = QAction("Write Program", self)
        self._a_write_program.setToolTip(
            "割り当て ASM を仮想回路（CPU/RAM）へ書き込む（実機書き込みではない）"
        )
        self._a_write_program.triggered.connect(lambda: self.write_program())

        self._a_run = QAction("Run", self)
        self._a_run.setShortcut(QKeySequence("Ctrl+R"))
        self._a_run.triggered.connect(self._do_run)

        self._a_pause = QAction("Pause", self)
        self._a_pause.setShortcut(QKeySequence("F6"))
        self._a_pause.triggered.connect(self._do_pause)

        # Canvas view actions
        self._a_zoom_in = QAction("Zoom In", self)
        self._a_zoom_in.setShortcut(QKeySequence("Ctrl+="))
        self._a_zoom_in.triggered.connect(self._canvas.zoom_in)

        self._a_zoom_out = QAction("Zoom Out", self)
        self._a_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        self._a_zoom_out.triggered.connect(self._canvas.zoom_out)

        self._a_zoom_reset = QAction("Reset Zoom", self)
        self._a_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        self._a_zoom_reset.triggered.connect(self._canvas.reset_zoom)

        self._a_fit = QAction("Fit", self)
        self._a_fit.triggered.connect(self._canvas.fit_to_view)

        self._a_grid = QAction("Grid", self)
        self._a_grid.setCheckable(True)
        self._a_grid.setChecked(True)
        self._a_grid.triggered.connect(self._canvas.set_grid_visible)

        self._a_snap = QAction("Snap", self)
        self._a_snap.setCheckable(True)
        self._a_snap.setChecked(False)
        self._a_snap.triggered.connect(self._canvas.set_snap)

        self._a_wire_mode = QAction("Wire Mode", self)
        self._a_wire_mode.setCheckable(True)
        self._a_wire_mode.setChecked(False)
        self._a_wire_mode.triggered.connect(
            lambda checked: self._canvas.set_mode("wire" if checked else "design")
        )
        self._canvas.mode_changed.connect(self._on_mode_changed)

        # Wiring ribbon actions (Patch 2 F)
        self._a_cancel_wire = QAction("Cancel Wire", self)
        self._a_cancel_wire.triggered.connect(self._cancel_wire_action)

        # Parts ribbon actions (Patch 2 C)
        self._a_import_part = QAction("Import Part…", self)
        self._a_import_part.setEnabled(False)   # not a dead button: clearly disabled
        self._a_import_part.setToolTip(
            "外部パーツ定義の取り込み（次パッチで対応予定）"
        )

        self._a_open_parts_folder = QAction("Open Parts Folder", self)
        self._a_open_parts_folder.triggered.connect(self._open_parts_folder)

        # Register with the window so keyboard shortcuts remain active
        for a in (self._a_build, self._a_reset, self._a_step,
                  self._a_run, self._a_pause,
                  self._a_zoom_in, self._a_zoom_out, self._a_zoom_reset,
                  self._a_fit):
            self.addAction(a)

    def _setup_toolbar(self):
        # v0.5 UI Prototype Patch 2 — purpose-based ribbon tabs.
        # Project tab removed (A): New/Open/Save/Save As stay in the File menu.
        self._ribbon = RibbonBar()
        self._ribbon.add_page("Parts", [           # C: meaningful operations only
            self._parts_lib_dock.toggleViewAction(),
            self._a_import_part,
            self._a_open_parts_folder,
        ])
        self._ribbon.add_page("Wiring", [
            self._a_wire_mode, self._a_cancel_wire,
        ])
        self._ribbon.add_page("Run", [
            self._a_build, self._a_write_program,
            self._a_run, self._a_step, self._a_reset, self._a_pause,
        ])
        self._ribbon.add_page("View", [            # H: no Zoom In/Out (wheel zoom stays)
            self._a_grid, self._a_snap,
            self._a_zoom_reset, self._a_fit,
            self._props_dock.toggleViewAction(),
        ])
        self._ribbon.add_page("Debug", [           # I: Log and Console separated
            self._run_status.toggleViewAction(),
            self._port_detail.toggleViewAction(),
            self._address_map_editor.toggleViewAction(),
            self._reg_view_dock.toggleViewAction(),
            self._mem_viewer.toggleViewAction(),
            self._bus_trace_dock.toggleViewAction(),
            self._uart_console_dock.toggleViewAction(),
            self._log_dock.toggleViewAction(),
            self._console_dock.toggleViewAction(),
        ])

        tb = QToolBar("Ribbon", self)
        tb.setMovable(False)
        tb.addWidget(self._ribbon)
        self.addToolBar(tb)
        self._toolbar = tb
