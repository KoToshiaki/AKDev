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

**v0.6 PHASE COMPLETE (2026-06-16)** — UI Polish & Usability plus the Virtual Circuit
Runtime foundation (Program/Sources assignment, Write Program, Virtual CPU Step & Trace,
Canvas-derived CircuitPlan, connectivity-gated Write/Build/Run/Step). `pytest tests/`
= 779 passed.

Current phase: **v0.7 — Plan-driven Virtual Devices & Address Map**. See
[ROADMAP7.md](ROADMAP7.md) / [CHECKLIST7.md](CHECKLIST7.md). The completed v0.6 phase
plan is in [ROADMAP6.md](ROADMAP6.md) / [CHECKLIST6.md](CHECKLIST6.md) (kept for history;
completed patch docs archived under `old/`).
