# ROM File Format Specification

## File Extension

`.rom`

## Header (64 bytes)

| Offset | Size | Field       | Description          |
|-------:|------|-------------|----------------------|
|      0 |    4 | magic       | `AKR1` (0x414B5231) |
|      4 |    4 | version     | Format version       |
|      8 |    4 | entry       | Entry point address  |
|     12 |    4 | code_off    | Code section offset  |
|     16 |    4 | code_len    | Code section length  |
|     20 |    4 | asset_off   | Asset section offset |
|     24 |    4 | asset_len   | Asset section length |
|     28 |    4 | meta_off    | Metadata offset      |
|     32 |    4 | meta_len    | Metadata length      |
|     36 |   28 | reserved    | Zero-padded          |

## Sections

- **code**: Raw binary, loaded to Boot ROM area (0x00000000)
- **asset**: Raw binary assets (tiles, sprites, maps)
- **meta**: UTF-8 JSON metadata (name, version, author)

## Loading

1. Verify magic = `AKR1`
2. Load code to 0x00000000
3. Set PC = entry
4. ROM is not in v0.1 — placeholder spec only.
