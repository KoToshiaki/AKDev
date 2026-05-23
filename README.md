# AKDev

AKDev is an integrated development environment and simulator for a custom FPGA game console.

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

## v0.1 Quick Start

1. Launch the app:
   ```
   python main.py
   ```

2. In the **System Canvas**, double-click the AK32 CPU part from the Parts Library.

3. Right-click the CPU node and select **"Open Program"** to open an `.asm` editor tab.

4. Paste or type the hello world program (see `src/hello.asm`):
   ```asm
   LDI r2, 0x100    # UART base address
   LDI r1, 72       # 'H'
   OUT [r2], r1
   LDI r1, 105      # 'i'
   OUT [r2], r1
   HALT
   ```

5. Press **F5** (Build) — the binary is assembled and loaded into the simulator RAM.

6. Press **Ctrl+Shift+R** (Reset) to reset the CPU.

7. Press **Ctrl+R** (Run) to execute.

8. Check the panels at the bottom / right:
   - **UART Console** — shows `Hi`
   - **Register View** — `r1 = 0x00000069`, `halted = HALTED`
   - **Bus Trace** — shows two `WRITE addr=0x0100` entries (0x48 and 0x69)

## Status

v0.1 complete — see `CHECKLIST2.md` for details and `ROADMAP2.md` for next steps.
