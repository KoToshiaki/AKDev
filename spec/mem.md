# Memory Map Specification

## Address Map

| Range                       | Size   | Description         |
|-----------------------------|--------|---------------------|
| 0x00000000 - 0x0000FFFF     | 64 KiB | Boot ROM            |
| 0x10000000 - 0x10FFFFFF     | 16 MiB | Main RAM            |
| 0x20000000 - 0x200000FF     | 256 B  | UART                |
| 0x20000100 - 0x200001FF     | 256 B  | Timer               |
| 0x20000200 - 0x200002FF     | 256 B  | Input               |
| 0x20000300 - 0x200003FF     | 256 B  | Power Monitor       |
| 0x30000000 - 0x30000FFF     | 4 KiB  | Graphics Registers  |
| 0x40000000 - 0x40FFFFFF     | 16 MiB | VRAM Window         |

## Access Width

- All bus transactions are 32-bit (word).
- Byte / halfword access: TBD in v0.2.

## Alignment

- Word access must be 4-byte aligned.
- Unaligned access raises a bus error in simulation.

## Shared Definition

This file is the single source of truth for address constants.
All simulator, assembler, and HDL files must reference these values.
