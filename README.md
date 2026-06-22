# AKDev

AKDev is an integrated development and simulation environment for a custom FPGA game console built around the AK32 CPU architecture.

## What you can do with v0.4.1

- Place CPU, RAM, UART, and other parts on a visual System Canvas
- Connect parts with obstacle-aware Manhattan routing (BFS)
- Write AK32 assembly (NOP/HALT/LDI/OUT/ADD/SUB/LD/ST/JMP/BEQ/ADDI/AND/OR/XOR/NOT)
- Build (F5) and Run the program in the built-in simulator
- Step through instructions one at a time
- View CPU registers, UART output, bus transactions, and memory hex dump
- See the current PC highlighted in the editor and on the canvas signal overlay
- Save and reload projects (Canvas layout + source files)

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

## Documentation

- **[Quick Start](docs/QUICKSTART.md)** — 5 分で hello.asm を動かす手順
- **[User Guide](docs/USER_GUIDE.md)** — 全機能の詳細説明

## Sample programs

| File | Description |
|---|---|
| `src/hello.asm` | Output "Hi" to UART using LDI / OUT / HALT |
| `src/fib.asm` | Fibonacci sequence using ADD / ST / ADDI / BEQ / JMP |

## Canvas controls (v0.4.1)

| Input | Action |
|---|---|
| Left-drag | Select / move parts |
| Right-click | Context menu / wire mode |
| Middle-drag | Pan canvas |
| Wheel | Zoom in / out |

## What's new in v0.8 (Device Expansion & Connection Validation)

- **More devices**: in addition to CPU / RAM / UART, you can now place **Input** (MMIO,
  read with `LD`), **ROM** (read-only memory), **Timer** (deterministic per-step tick,
  read/clear with `LD`/`ST`) and **VRAM** (writable 32×32 framebuffer, written with `ST`).
- **ROM target**: choose whether `Write Program` loads into RAM or ROM (ROM target resets
  the CPU to the ROM base and fetches code from ROM).
- **Address Map Editor**: per-device base/size override (auto/manual) with overlap/range
  validation, on top of a configurable `MemoryLayout` (LEGACY / CIRCUIT_COMPAT / GAME16).
- **Connection validation** (warning only): port direction/width and bus master/slave checks.
- **AK32 bitwise**: `AND` / `OR` / `XOR` / `NOT` (enables reading individual input bits).
- **Minimal game runtime**: ROM + Input + Timer + VRAM running together — execute from ROM,
  read Input/Timer, draw to VRAM — shown in a small **32×32 grayscale VRAM Viewer** that
  refreshes after Step/Run/Reset.

Devices: **CPU / RAM / UART / Input / ROM / Timer / VRAM**.
Execution: **RAM target / ROM target / Address Map Editor / Run Status / VRAM Viewer**.

## Test

```
python -m pytest tests/
```

## Status

**v0.8 complete (2026-06-23)** — Device Expansion & Connection Validation (14 patches,
`PATCH_PORT_SCHEMA_V08` … `PATCH_GAME_RUNTIME_MINIMAL_V08`, finalized by
`PATCH_V08_STABILIZE_AND_DOCS`). Builds on the v0.7 plan-driven execution base
(circuit-mode 64 KB RAM, UART MMIO window, Address Map, Run Status / Port Detail panels)
by adding Input / ROM / Timer / VRAM devices, RAM/ROM program targets, the Address Map
Editor, AK32 bitwise instructions and a minimal ROM+Input+Timer+VRAM game runtime with a
32×32 VRAM Viewer. Existing projects without the new devices are unchanged; legacy mode
(no CPU on canvas) is unchanged. `pytest tests/` = **1182 passed**. `PHASE COMPLETE` is a
user-declared step (archiving to `old/` and creating the v0.9 plan happen afterwards).

The live planning files are [ROADMAP8.md](ROADMAP8.md) / [CHECKLIST8.md](CHECKLIST8.md);
per-patch design docs are `PATCH_*_V08_*.md`. Completed phase plans are archived under
`old/` (kept for history, not deleted): the v0.7 plan in [old/ROADMAP7.md](old/ROADMAP7.md)
/ [old/CHECKLIST7.md](old/CHECKLIST7.md), the v0.6 plan in [old/ROADMAP6.md](old/ROADMAP6.md)
/ [old/CHECKLIST6.md](old/CHECKLIST6.md). v0.9 candidates (branch/shift/stack instructions,
VRAM Viewer & game-runtime expansion, sprite/tile/palette, HDL/FPGA export) are listed in
ROADMAP8.md.
