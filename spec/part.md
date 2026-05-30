# Part Definition Specification

## File: `part.json`

Each part lives in its own directory under `parts/<category>/<name>/`.

### Required Fields

| Field    | Type   | Description              |
|----------|--------|--------------------------|
| id       | string | Unique ID, e.g. `cpu.ak32` |
| name     | string | Display name             |
| category | string | `fpga`, `cpu`, `mem`, `io`, `video`, `custom` |
| ports    | array  | List of port objects     |

### Optional Fields

| Field     | Type   | Description                     |
|-----------|--------|---------------------------------|
| resources | object | LUT, BRAM, DSP counts           |
| editable  | array  | Editable files (asm, hdl, etc.) |
| sim       | string | Simulator module filename       |
| description | string | Short description             |

### Port Object

```json
{"name": "bus", "type": "bus.slave"}
```

### Port Types

`bus.master`, `bus.slave`, `clock`, `reset`, `irq`,
`gpio`, `video.rgb`, `audio.pwm`, `debug.jtag`,
`serial.uart`, `spi.master`, `spi.slave`,
`i2c.master`, `i2c.slave`

### Example

```json
{
  "id": "cpu.ak32",
  "name": "AK32 CPU",
  "category": "cpu",
  "description": "Custom 32-bit RISC CPU",
  "ports": [
    {"name": "bus", "type": "bus.master"},
    {"name": "clk",  "type": "clock"},
    {"name": "reset","type": "reset"},
    {"name": "irq",  "type": "irq"}
  ],
  "editable": [{"name": "program", "type": "asm"}],
  "sim": "sim.py"
}
```
