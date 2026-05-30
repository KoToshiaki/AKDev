# GPU / Graphics Register Specification

## Base Address

`0x30000000`

## Registers

| Offset | Name       | R/W | Description        |
|-------:|------------|-----|--------------------|
|   0x00 | GFX_ID     | R   | Fixed identifier   |
|   0x04 | STATUS     | R   | READY / BUSY flag  |
|   0x08 | BG_COLOR   | R/W | Background colour  |
|   0x0C | CMD        | W   | Command register   |
|   0x10 | ARG0       | W   | Command argument 0 |
|   0x14 | ARG1       | W   | Command argument 1 |
|   0x18 | ARG2       | W   | Command argument 2 |
|   0x1C | IRQ_EN     | R/W | IRQ enable         |
|   0x20 | IRQ_FLAG   | R/W | IRQ status         |

## Commands

| ID | Name       | Args              |
|----|------------|-------------------|
|  0 | NOP        | -                 |
|  1 | CLEAR      | -                 |
|  2 | SET_BG     | color             |
|  3 | DRAW_RECT  | x, y, w, h        |
|  4 | COPY       | src, dst, len     |
|  5 | LOAD_TILE  | tile_id, addr     |
|  6 | SET_SPRITE | sprite_id, params |

## Not in v0.1

- Multiple background layers
- Sprite priority
- Alpha blending
- Rotation / scaling
- 3D pipeline
