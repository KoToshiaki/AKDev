# AK32 CPU Specification

## Registers

| Name   | Description         |
|--------|---------------------|
| r0     | Always 0 (read-only)|
| r1-r12 | General purpose     |
| r13    | Stack pointer (sp)  |
| r14    | Link register (lr)  |
| r15    | Reserved / general  |
| pc     | Program counter     |
| flags  | Z, N, C, V          |

## Instruction Set

All instructions are 32-bit wide.

```
NOP
HALT
LDI  rd, imm
LD   rd, [ra + imm]
ST   rs, [ra + imm]
ADD  rd, ra, rb
SUB  rd, ra, rb
AND  rd, ra, rb
OR   rd, ra, rb
XOR  rd, ra, rb
SHL  rd, ra, imm
SHR  rd, ra, imm
JMP  addr
BEQ  ra, rb, offset
BNE  ra, rb, offset
CALL addr
RET
IN   rd, [addr]
OUT  [addr], rs
```

## Encoding (preliminary)

| Field  | Bits  |
|--------|-------|
| opcode | 31-24 |
| rd/rs  | 23-20 |
| ra     | 19-16 |
| rb     | 15-12 |
| imm    | 11-0  |

## Reset

- PC = 0x00000000
- All registers = 0
- flags = 0

## Not in v0.1

- Multiply / divide
- Interrupts
- Cache
- Pipeline
- Privilege modes
- MMU
