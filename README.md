# AKDev

**Language / 言語: English | [日本語](README.ja.md)**

AKDev is an integrated development and simulation environment for a custom FPGA game
console built around the **AK32 CPU architecture**. You place CPU / memory / I/O parts on
a visual System Canvas, wire them into a circuit, write **AK32 assembly**, and Build / Run /
Step the program on a built-in virtual machine — with the CPU, RAM, UART, Input, ROM, Timer
and VRAM all simulated in software. It is aimed at eventually building and running a small
game on a self-made CPU, with FPGA / HDL export as a longer-term goal.

> **Physically this runs as a Python program on a PC.** Internally AKDev keeps virtual CPU /
> memory / device state and executes AK32 instructions one at a time (Step = 1 instruction,
> Run = repeated Step). "Write Program" loads code into the virtual circuit — it is **not**
> real FPGA programming.

---

## Overview

- **Visual System Canvas** — place and wire parts (CPU, RAM, UART, Input, ROM, Timer, VRAM).
- **AK32 assembly** — 15 instructions (`NOP HALT LDI OUT ADD SUB LD ST JMP BEQ ADDI AND OR XOR NOT`).
- **Virtual machine** — Build / Write Program / Run / Step / Reset with full instruction trace.
- **Devices** — CPU plus writable RAM, MMIO UART, MMIO Input, read-only ROM, deterministic
  Timer, and a writable 32×32 VRAM framebuffer.
- **Memory model** — configurable `MemoryLayout`, an Address Map with overlap detection, and
  an Address Map Editor for per-device base/size overrides.
- **Program targets** — load a program into RAM (default) or ROM (fetch-from-ROM).
- **Minimal game runtime** — ROM + Input + Timer + VRAM running together, with a small
  32×32 grayscale VRAM Viewer.
- **Debug panels** — registers, memory hex dump, bus trace, UART console, Run Status,
  Port Detail, Address Map Editor, VRAM Viewer, PC highlight, signal overlay.
- **Projects** — save / reload the Canvas layout, source assignments, program target and
  address-map overrides.

---

## Current Status

**v0.8 complete (2026-06-23) — Device Expansion & Connection Validation.**

- Delivered as 14 patches (`PATCH_PORT_SCHEMA_V08` … `PATCH_GAME_RUNTIME_MINIMAL_V08`),
  finalized by `PATCH_V08_STABILIZE_AND_DOCS`.
- `python -m pytest tests/` → **1182 passed**. The 21 warnings are PySide6 `Deprecation`
  notices only (no test failures).
- `tests/test/system.json` has **no diff** (test runs do not change tracked fixtures).
- Existing projects without the new devices are unchanged; legacy mode (no CPU on canvas)
  is unchanged.
- **v0.9 is intentionally undecided** — the focus is chosen by the user after reviewing the
  current capabilities (see [v0.9 Planning Candidates](#v09-planning-candidates)). `PHASE
  COMPLETE` for v0.8 **has been declared and processed** (v0.8 plans archived to `old/`,
  [ROADMAP9.md](ROADMAP9.md) / [CHECKLIST9.md](CHECKLIST9.md) created). v0.9 implementation
  has **not** started.

---

## Feature Overview

| Area | What you can do today |
|---|---|
| Visual Canvas | Place / select / move / wire parts; pan / zoom; inspect via panels |
| Connection validation | Port direction/width and bus master/slave checks (**warning only**, never blocks) |
| AK32 Assembly | Write/edit `.asm`, assemble with labels, 15 instructions |
| Build / Write | Assemble and load a program into the virtual circuit (RAM or ROM) |
| Run / Step / Reset | Execute the program with a full per-instruction trace |
| Devices | CPU, RAM, UART, Input, ROM, Timer, VRAM |
| Memory / Address Map | Layout-driven base/size, overlap detection, per-device overrides |
| VRAM Viewer | 32×32 grayscale framebuffer view, refreshed after Step/Run/Reset |
| Minimal game runtime | ROM + Input + Timer + VRAM together (execute from ROM, read input/timer, draw to VRAM) |
| Projects | Save/reload Canvas + sources + program target + address overrides |
| Tests | `pytest tests/` → 1182 passed |

---

## Visual Canvas

You build a system by dropping parts from the Parts Library onto the Canvas and wiring them.

| Input | Action |
|---|---|
| Left-drag | Select / move a part |
| Left-click a wire | Select the wire (Properties switches to Wire view) |
| Left-drag from a visual port | Start a connection to another part |
| Alt + left-drag a visual port | Move the port along the node edge (connected wires follow) |
| Right-click | Context menu (wire mode, set ASM source, delete, etc.) |
| Middle-drag | Pan the canvas |
| Wheel | Zoom in / out |
| Delete | Delete the selected wire, otherwise the selected node |

Canvas details:

- **Parts start with no fixed ports**; a *visual port* is created at the connection point
  when you wire two parts (the connection stores both the visual port and the logical port).
- **Wires** are drawn as curved connections between visual ports and follow nodes/ports when
  they move. Fan-out (multiple wires from one port) is supported.
- **Selection** drives the side panels: selecting a node shows its **Properties** and
  **Port Detail**; selecting a wire shows its style.
- The **Run Status**, **Port Detail** and **Address Map Editor** panels update on
  selection, wiring changes, and Write/Build/Run/Step/Reset.

---

## Devices

All devices live on the CPU bus. Memory-role devices (RAM/ROM/VRAM) are addressable regions;
MMIO-role devices (UART/Input/Timer) occupy small register windows. The CPU reaches every
device through the existing `LD` / `ST` (and `OUT`) — **no special I/O instruction**.

| Device | Part ID | Role | Runtime ID | Access | What it does | Notes |
|---|---|---|---|---|---|---|
| CPU | `cpu.ak32` | cpu | `sim_cpu` | — | Executes AK32 instructions | reset PC comes from the layout / ROM target |
| RAM | `mem.ram` | memory | `sim_ram` | `LD` / `ST` | Read/write working memory | 32-bit LE words; **cleared to 0 on reset** |
| UART | `io.uart` | mmio | `sim_uart` | `OUT` / `ST` (write), `LD` (status) | Collects written bytes as text output | `+0` DATA (write byte), `+4` STATUS (TX ready) |
| Input | `io.input` | mmio | `sim_input` | `LD` (read) | Reads held keys / edges | `+0` KEY_STATE, `+4` EDGE_STATE; driven from UI/tests |
| ROM | `mem.rom` | memory | `sim_rom` | `LD` (read) | Read-only program/firmware memory | CPU/bus writes are a no-op; **survives reset**; used by ROM target |
| Timer | `io.timer` | mmio | `sim_timer` | `LD` (read), `ST` (clear) | Deterministic step counter | `+0` TICK, `+4` DELTA; +1 per executed instruction; no interrupts |
| VRAM | `mem.vram` | memory | `sim_vram` | `LD` / `ST` | Writable 32×32 framebuffer | 1 byte/pixel, 1024 B; `dump()`/`pixel()`; **cleared on reset** |

Only the **first** device of each kind is turned into a runtime part; additional UART/RAM/etc.
are placed/diagnosed on the Address Map but not executed (full multi-device runtime is future
work). A device that is not placed at all is simply absent — projects without it are unchanged.

---

## AK32 Assembly

15 instructions are implemented. Registers are `r0`–`r15`. Immediates accept decimal or `0x`
hex. `[rX]` means "memory at the address in rX". Labels (`name:`) are supported; `JMP` takes
a label/address and `BEQ` takes a label (PC-relative).

| Instruction | Form | Meaning | Example |
|---|---|---|---|
| `NOP` | `NOP` | Do nothing | `NOP` |
| `HALT` | `HALT` | Stop the CPU | `HALT` |
| `LDI` | `LDI rd, imm16` | Load 16-bit immediate | `LDI r1, 0xC000` |
| `OUT` | `OUT [ra], rs` | Write rs to the device at [ra] | `OUT [r2], r1` |
| `ADD` | `ADD rd, rs, rt` | rd = rs + rt | `ADD r3, r1, r2` |
| `SUB` | `SUB rd, rs, rt` | rd = rs − rt | `SUB r3, r1, r2` |
| `LD` | `LD rd, [rs]` | Load word from memory/MMIO at [rs] | `LD r2, [r1]` |
| `ST` | `ST [rd], rs` | Store word rs to memory/MMIO at [rd] | `ST [r1], r2` |
| `JMP` | `JMP target` | Unconditional jump | `JMP loop` |
| `BEQ` | `BEQ rs, rt, target` | Branch to target if rs == rt | `BEQ r1, r0, done` |
| `ADDI` | `ADDI rd, rs, imm8` | rd = rs + imm8 | `ADDI r2, r2, 1` |
| `AND` | `AND rd, rs, rt` | rd = rs & rt | `AND r3, r1, r2` |
| `OR` | `OR rd, rs, rt` | rd = rs \| rt | `OR r3, r1, r2` |
| `XOR` | `XOR rd, rs, rt` | rd = rs ^ rt | `XOR r3, r1, r2` |
| `NOT` | `NOT rd, rs` | rd = ~rs | `NOT r3, r1` |

**Not yet implemented** (planned for v0.9): `BNE` / `BEQZ` / `BNEZ` (extra branches),
`SHL` / `SHR` / `ANDI` / `ORI` (shift & immediate bitwise), `CALL` / `RET` / stack. There is
**no `IN` instruction** — Input is read with `LD` because it is memory-mapped. Bit testing
uses `LD` + `AND` + `BEQ`.

---

## Build / Write / Run

### Program targets

`Write Program` assembles the assigned `.asm` and loads it into the virtual circuit. The
**program target** selects where:

- **RAM target** (default, fully backward-compatible): the program is loaded into RAM and the
  CPU starts at the layout reset PC (default `0x0000`). This is the original behaviour.
- **ROM target**: the program is loaded into ROM and the CPU `reset_pc` is set to the ROM
  base, so it fetches code from ROM. If ROM is not viable (no ROM device, not placed, overlap,
  or size exceeded) it is an **error** — it does **not** silently fall back to RAM. ROM content
  survives reset; CPU/bus writes to ROM are ignored.

### Run / Step / Reset

- **Step** executes exactly one instruction and updates every debug panel.
- **Run** repeats Step (up to a 1000-instruction cap, or until `HALT` / pause).
- Each step produces a trace (PC before/after, decoded instruction, register changes, memory
  and I/O accesses, UART output, halted/error), surfaced in the Log, Bus Trace and Run Status.
- The **Timer** advances one tick per executed instruction, so timing is fully reproducible.
- **Reset** resets the CPU and runtime: RAM and VRAM clear to 0, the Timer resets, ROM keeps
  its image. Reset also refreshes the panels (including the VRAM Viewer).

---

## Memory Layout and Address Map

The **Address Map** is the layout of devices on the 16-bit bus (each device's base / size /
end and attach ranges), with overlap and range detection.

- **MemoryLayout** presets decide default base/size:

  | Layout | RAM | ROM | VRAM | MMIO base |
  |---|---|---|---|---|
  | `LEGACY` | `0x0000` / 256 B | — | — | `0x0100` |
  | `CIRCUIT_COMPAT` (default) | `0x0000` / 64 KB | — (override) | — (override) | `0x0100` (inside RAM) |
  | `GAME16` | `0x8000` / 16 KB | `0x0000` / 32 KB | `0xC000` / 1 KB | `0xE000` |

- **MMIO addresses are assigned in placement order**: UART / Input / Timer land at
  `MMIO base`, `+0x10`, `+0x20`, … So in GAME16 they are typically `0xE000` / `0xE010` /
  `0xE020`, and in CIRCUIT_COMPAT `0x0100` / `0x0110` / `0x0120`. **Confirm the actual base in
  the Address Map / Run Status before hardcoding it in a program.**
- **Address Map Editor** (dock panel) lets you override per-device `base` / `size`
  (auto ↔ manual), Reset to Auto, and validates range / overlap / alignment. Overrides are
  persisted into the project's `system.json`. With no overrides the layout is fully automatic
  (current default behaviour).
- The interactive MainWin auto-selects `CIRCUIT_COMPAT`; `GAME16` is exercised via tests and
  via Editor overrides that reproduce its map (e.g. VRAM at `0xC000` with RAM shrunk).
- This patch family does **not** change `tests/test/system.json`.

---

## Input / Timer / VRAM

### Input (MMIO, read with `LD`)

- Register window: `+0` **KEY_STATE** (currently-held key bitmask), `+4` **EDGE_STATE** (keys
  pressed since the last clear; writing to EDGE_STATE clears it).
- Key bits: `0` up, `1` down, `2` left, `3` right, `4` A, `5` B, `6` Start, `7` Select.
- The CPU reads keys with `LD`; test individual bits with `AND` + `BEQ`. Input state is driven
  from the UI / tests (no `IN` instruction needed).

### Timer (MMIO, `LD` to read / `ST` to clear)

- Deterministic: it counts **CPU steps**, not wall-clock time, so runs are reproducible.
- Register window: `+0` **TICK** (monotonic step count; writing clears it), `+4` **DELTA**
  (ticks since the last DELTA clear; writing rebases it to "now").
- Read with `LD`, clear with `ST`. There are **no interrupts** yet.

### VRAM (writable framebuffer)

- A memory device: 32×32 pixels, **1 byte per pixel** (indexed value), 1024 bytes total.
- The CPU writes with `ST` and reads with `LD` (32-bit LE words; one word = 4 horizontal
  pixels). Helpers `dump()` / `pixel(x, y)` / `set_pixel(x, y, v)` expose the framebuffer.
- Cleared to 0 on reset. The contents are shown in the **VRAM Viewer**.
- **No palette / sprites / tiles** yet — the value is rendered as a grayscale level.

---

## Minimal Game Runtime

The "game-like" behaviour available today is a **minimal** runtime, not a game engine:

- Place **ROM + Input + Timer + VRAM** together (alongside CPU/RAM/UART).
- Run from **ROM target**: the CPU fetches code from ROM.
- The program reads **Input** and **Timer** with `LD` and draws to **VRAM** with `ST`.
- The **VRAM Viewer** (a small dock) shows the 32×32 framebuffer as a scaled grayscale image
  and refreshes after Step / Run / Reset / Write.
- No new `GameRuntime` class was added: it runs on the **existing Run/Step** loop, and **no
  CPU instruction or ASM syntax was changed**. The Run Status panel shows a `Game:` line with
  the active devices (e.g. `ROM+Input+Timer+VRAM`).

This is the v0.8 endpoint: enough to prove ROM + Input + Timer + VRAM working together and a
visible framebuffer. Sprites, tiles, palettes, audio, frame sync and a real game loop are
**not** included (see Known Limitations / v0.9 candidates).

---

## Debug Panels

| Panel | Shows |
|---|---|
| UART Console | Accumulated UART text output |
| Console / Log | Build/run messages and per-step trace |
| Register View | CPU registers, PC, cycle |
| Memory Viewer | Hex dump of simulator RAM (with PC row highlight) |
| Bus Trace | Recent bus read/write transactions |
| Run Status | Mode, program target, Timer/VRAM/Game lines, target CPU, Address Map, last trace, UART |
| Port Detail | Logical/visual ports, direction/width, connections, wire detail |
| Address Map Editor | Per-device base/size view + override (auto/manual) + validation |
| VRAM Viewer | 32×32 grayscale framebuffer (or `VRAM: None` when unplaced) |
| Canvas overlays | PC highlight in the editor and on the canvas; signal overlay during Run |

---

## Project Save / Load

A saved project (`system.json`) currently includes:

- the **Canvas layout** (nodes, positions, visual ports, wires/connections and wire styles),
- per-part **source assignments** (`sources.asm` / `hdl` / `rom` paths),
- the **program target** (`ram` / `rom`),
- **Address Map overrides** (per-device base/size).

Not yet persisted: the loaded program image itself (`loaded_program` is session-only).
Stronger save/load (program persistence, portability) is a v0.9 candidate.

---

## Sample Programs

Existing samples:

| File | Description |
|---|---|
| `src/hello.asm` | Output "Hi" to the UART using `LDI` / `OUT` / `HALT` |
| `src/fib.asm` | Fibonacci using `ADD` / `ST` / `ADDI` / `BEQ` / `JMP` |

Minimal VRAM / device snippets (implemented instructions only). Addresses below assume the
**GAME16** map (VRAM at `0xC000`); MMIO bases for Input/Timer depend on placement order, so
**read the actual base from the Address Map / Run Status** before relying on it.

Write a fixed value to VRAM:

```asm
LDI r1, 0xC000      ; VRAM base (GAME16)
LDI r2, 0x00FF      ; pixel value
ST  [r1], r2        ; VRAM[0] = 0xFF
HALT
```

Copy the Timer tick into VRAM (replace `<TIMER_BASE>` with the address shown in the Address Map):

```asm
LDI r1, <TIMER_BASE>  ; e.g. 0xE020 in GAME16 — confirm in the Address Map
LD  r2, [r1]          ; read TICK
LDI r3, 0xC000
ST  [r3], r2          ; VRAM[0] = tick
HALT
```

Copy the Input state into VRAM (replace `<INPUT_BASE>` with the address shown in the Address Map):

```asm
LDI r1, <INPUT_BASE>  ; e.g. 0xE010 in GAME16 — confirm in the Address Map
LD  r2, [r1]          ; read KEY_STATE
LDI r3, 0xC000
ST  [r3], r2          ; VRAM[0] = keys
HALT
```

---

## Requirements

- Python 3.11+
- PySide6

## Setup

```
pip install -r requirements.txt
```

## Run

```
python main.py
```

## Test

```
python -m pytest tests/
```

Current result: **1182 passed** (21 warnings are PySide6 `Deprecation` notices only). GUI
visual confirmation (e.g. how the VRAM Viewer looks, Run Status lines on screen) is **not**
done in the headless test environment; the underlying logic (framebuffer rendering via
`snapshot()` / `pixel()`, status formatting) is covered by `pytest`.

---

## Known Limitations

- **GUI visual confirmation** is partly unverified (headless tests cover logic, not on-screen
  appearance).
- **VRAM Viewer** is minimal: 32×32 grayscale only — no palette / color UI / zoom controls.
- **No sprites / tiles**, **no palette** (the byte value is shown as a gray level).
- **No audio**, **no DMA / GPU**, **no physics / asset system**.
- **No HDL / FPGA export** yet.
- **Instruction set gaps**: no extra branches (`BNE` / `BEQZ` / `BNEZ`), no shift / immediate
  bitwise (`SHL` / `SHR` / `ANDI` / `ORI`), no stack / `CALL` / `RET`.
- **No full game runtime** — the minimal runtime proves device integration, not a game loop.
- **No bundled project template / sample game project** yet.
- **Multiple RAM/UART**: extra devices are placed/diagnosed but only the first of each kind
  runs; true multi-RAM coexistence is unsolved (16-bit address space constraint).
- The handling of `tests/test/system.json` test-run diffs (discard / commit / gitignore) is a
  carried-over decision for the user.

---

## v0.9 Planning Candidates

The direction of v0.9 is **intentionally undecided**. The user will decide the v0.9 focus
after reviewing the current capabilities above. Candidates (not committed, no priority set):

- AK32 **branch expansion** (`BNE` / `BEQZ` / `BNEZ`)
- **Shift / immediate bitwise** (`SHL` / `SHR` / `ANDI` / `ORI`)
- **Stack / `CALL` / `RET`**
- **VRAM Viewer expansion** (palette / color / zoom UI)
- **Game Runtime expansion** (frame sync / input edges / a real game loop / multiple VRAM)
- **Sprite / tile / palette** graphics
- **HDL / FPGA export** preparation
- **Project template / sample project**
- **Save/load enhancement** (program persistence, portability)
- **GUI polish**
- **Packaging / release** preparation

---

## Documentation

- **[Quick Start](docs/QUICKSTART.md)** — 5 分で hello.asm を動かす手順
- **[User Guide](docs/USER_GUIDE.md)** — 全機能の詳細説明
- **Planning**: [ROADMAP9.md](ROADMAP9.md) / [CHECKLIST9.md](CHECKLIST9.md) (v0.9 candidates,
  not yet started). Completed phase plans are archived under `old/` (kept for history):
  v0.8 in [old/ROADMAP8.md](old/ROADMAP8.md) / [old/CHECKLIST8.md](old/CHECKLIST8.md) with
  per-patch design docs `old/PATCH_*_V08_*.md`, v0.7 in [old/ROADMAP7.md](old/ROADMAP7.md) /
  [old/CHECKLIST7.md](old/CHECKLIST7.md), v0.6 in [old/ROADMAP6.md](old/ROADMAP6.md) /
  [old/CHECKLIST6.md](old/CHECKLIST6.md).
- **Handoff / current state**: [HANDOFF.md](HANDOFF.md).
