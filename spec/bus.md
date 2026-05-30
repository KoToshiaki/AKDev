# Bus Specification

## Bus Types

| Type        | Width | Description              |
|-------------|-------|--------------------------|
| bus32       | 32    | Standard 32-bit bus      |
| parallel16  | 16    | Chip-to-chip data bus    |
| parallel32  | 32    | Chip-to-chip (TBD)       |

## Transactions

- `read(addr)` → 32-bit value
- `write(addr, value)` — no return

## Address Decoding

The Bus uses a memory-map table to route transactions to the correct Part.

1. Scan map entries in priority order.
2. First match wins.
3. No match → bus error logged.

## Bus Trace Format

```
[cycle] PART OP addr = value  TARGET
[00001234] CPU WRITE 0x30000008 = 0x0000003F  GPU_BG
[00001235] GPU READ  0x30000000 = 0x47505500  GFX_ID
```

## Chip-to-Chip Bridge

chip0 and chip1 are connected via a bridge part.
Bridge latency: 1 cycle (simulated).
