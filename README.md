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

v0.4.1 — Visual Debug Canvas polish patch. See [ROADMAP5.md](ROADMAP5.md) for details.
