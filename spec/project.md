# Project File Format Specification

## Directory Layout

```
<project-name>/
├── project.json
├── system.json
├── src/
│   ├── main.asm
│   └── gpu_logic.v
├── asset/
│   ├── img/
│   ├── snd/
│   └── map/
├── build/
│   ├── main.bin
│   └── logs/
└── parts/
    └── custom/
```

## project.json

```json
{
  "name": "my_game",
  "created": "2026-05-22T00:00:00",
  "akdev_version": "0.1.0",
  "preset": "minimal_cpu",
  "last_open": ["src/main.asm"]
}
```

## system.json

```json
{
  "chips": [
    {"id": "chip0", "type": "fpga.ecp5_85f", "x": 200, "y": 120}
  ],
  "parts": [
    {"id": "cpu0", "type": "cpu.ak32", "parent": "chip0"},
    {"id": "ram0", "type": "mem.ram",  "parent": "chip0",
     "base": "0x10000000", "size": "16MiB"}
  ],
  "links": [
    {"from": "cpu0.bus", "to": "ram0.bus", "type": "bus32"}
  ]
}
```

## Versioning

`akdev_version` follows semver.  
A mismatch triggers a warning dialog on open.
