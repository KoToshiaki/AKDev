# AKDev

AKDev is an integrated development and simulation environment for a custom FPGA game console built around the AK32 CPU architecture.

## What you can do with v0.4.1

- Place CPU, RAM, UART, and other parts on a visual System Canvas
- Connect parts with obstacle-aware Manhattan routing (BFS)
- Write AK32 assembly (NOP/HALT/LDI/OUT/ADD/SUB/LD/ST/JMP/BEQ/ADDI)
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

## Status

**v0.7 PHASE COMPLETE (2026-06-17)** — Plan-driven Virtual Devices & Address Map.
The CPU+RAM+UART circuit drawn on the Canvas is now turned into real execution devices
(circuit mode 64 KB RAM with the UART as an MMIO window at `0x0100–0x0107`), with an
Address Map (base/size/overlap detection), CPU↔RAM ST/LD validation (`ram_selftest.asm`
→ UART `PASS`, plus Fibonacci), target-CPU selection for multi-CPU canvases, a Run Status
Panel (execution summary) and a Port Detail Panel (logical/visual ports, direction/width,
connections). Legacy mode (no CPU on canvas) is unchanged. `pytest tests/` = 860 passed.

Current phase: **v0.8 (candidates only)** — the live planning files are
[ROADMAP8.md](ROADMAP8.md) / [CHECKLIST8.md](CHECKLIST8.md). Completed phase plans are
archived under `old/` (kept for history, not deleted): the v0.7 plan in
[old/ROADMAP7.md](old/ROADMAP7.md) / [old/CHECKLIST7.md](old/CHECKLIST7.md), the v0.6 plan
in [old/ROADMAP6.md](old/ROADMAP6.md) / [old/CHECKLIST6.md](old/CHECKLIST6.md), along with
all completed patch docs.
