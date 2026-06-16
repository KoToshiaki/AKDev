# PATCH_VIRTUAL_CPU_STEP_TRACE_V05 — ROADMAP

> v0.5 進行中のパッチ。**PHASE COMPLETE ではない。**
> 進捗管理は `PATCH_VIRTUAL_CPU_STEP_TRACE_V05_CHECKLIST.md`。
> 親フェーズ: `ROADMAP6.md`（v0.5 UI Polish & Usability）。

---

## 目的

AKDev 内の**仮想 CPU 実行環境を明確化**し、1 命令ずつ Step 実行して
PC・命令・レジスタ変化・メモリ/IO アクセス・UART 出力を Log/Trace で詳しく
確認できるようにする。

> **重要（誤解防止）**: 「PC の CPU を使わずに実行する」という意味ではない。
> 物理的には PC 上の Python プログラムとして動く。ただし AKDev 内に
> **仮想 CPU・仮想 RAM・仮想 UART** の状態を持ち、命令を 1 つずつ
> fetch / decode / execute していることが分かる構造にする。

前提（完了済み）:

- `PATCH_CIRCUIT_WRITE_RUN_HELLO_V05` まで完了。
- `tests/test/hello_world.asm` が存在し、Write Program で仮想 CPU/RAM へロードできる。
- Run で UART Console に `Hello World !` を表示できる。
- `loaded_program` はセッション中 runtime 状態として保持。
- hello.asm headless 検証で UART `"Hi"` が通る。`pytest tests/` は 741 件全通過。

---

## 現状（実装前の調査結果）

| 領域 | 既存実装 |
|---|---|
| CPU emulator | `core/cpu.py` `AK32Part`。`tick()` が `bus.read(pc)` → `pc+=4` → `_execute(instr)`。11 命令 ISA。`regs()` / `pc()` / `z_flag()` / `halted()` アクセサあり |
| RAM | `core/dev.py` `RamPart`。`load_bytes` / `dump` / 32-bit LE word read/write |
| UART / IO | `core/dev.py` `UartPart`。base 0x100、`output_text()` に出力蓄積 |
| Bus | `core/sim.py` `Bus`。`tracing` で文字列 trace、`last_transactions` に最終トランザクション |
| MainWin 実行状態 | `ui/win.py` が `_sim_bus / _sim_ram / _sim_uart / _sim_cpu / _sim_cycle` を直接保持。`_do_step` は `_sim_cpu.tick()`、`_do_run` は最大 1000 回 tick |
| パネル更新 | `_update_register_view` / `_update_memory_viewer` / `_update_uart_console` / `_update_bus_trace` / `_update_signal_overlay` |
| 命令文字列 | disassembler は無い（`asm/asm.py` は assemble のみ、`address_map` あり）|

→ MainWin に散らばった実行状態を **Virtual Runtime** に寄せ、step が
1 命令分の詳細 trace を返す構造にする。既存 emulator はそのまま活かす（包む）。

---

## 設計

### 1. Virtual Runtime（`core/runtime.py` 新規）

`VirtualCircuitRuntime` — 既存の bus / ram / uart / cpu インスタンスを**受け取って包む**。
新規にデバイスを作らないことで Build/Run 互換を最優先する。

保持する状態:

- `cpu` / `ram` / `uart` / `bus`
- `loaded`（bool）/ `loaded_program`（dict or None）
- `step_count`
- `last_trace`
- `trace_history`（list[dict]）

最小 API:

```python
class VirtualCircuitRuntime:
    def load_program(self, binary, *, source_name="", target_node_id=None) -> None
    def reset(self) -> None
    def step(self) -> dict
    def run(self, max_steps: int = 10000) -> list[dict]
    def registers(self) -> dict
    def memory_snapshot(self) -> bytes
    def uart_text(self) -> str
```

### 2. 1 命令 Step Trace

`step()` は 1 命令を実行し、trace dict を返す。

```python
{
    "step": 3,
    "pc_before": 0x0008,
    "pc_after":  0x000C,
    "instruction": "OUT [r2], r1",   # 最小 disassembler
    "raw": 0x03020100,                # raw instruction word
    "register_changes": {"r1": ["0x00000000", "0x00000048"]},
    "memory": [],                     # RAM read/write（fetch は除外）
    "io": [{"type": "write", "addr": "0x0100", "value": "0x48", "device": "UART"}],
    "uart": "H",
    "halted": False,
    "error": None,
}
```

- メモリ/IO アクセスは **Bus に後方互換フック `on_access` を追加**して構造的に取得する
  （`core/sim.py`、既定 None で既存挙動不変）。
- 命令文字列は `core/runtime.py` の**最小 disassembler**（11 命令対応）で復元する。
  本格 disassembler ではない（将来拡張）。

### 3. Step ボタン

- 未ロード → `No program loaded. Use Write Program first.`
- halted 後 → `CPU is halted`
- 1 押下 = 1 命令。実行後 Register / Memory / Bus Trace / UART / signal overlay を更新。
- Log に `[STEP nnnn] PC .. -> .. | <instr>` + REG/MEM/IO/UART の詳細を出す。

### 4. Run の内部構造

- Run は `runtime.step()` の繰り返し（最大 1000、既存上限を維持）。
- halted で停止、上限到達でログ。
- `Hello World !` は従来どおり UART Console に出る。
- Log には**要約**（`Run finished: steps=.., halted=.., uart=".."`）。詳細は trace_history に保持。

### 5. Write Program 接続

- `Write Program` 成功で runtime に program がロード済みになる。
- `loaded_program` 表示は維持。`Write Program → Step` / `Write Program → Run` /
  `Build → Run` が成立する。

---

## 互換性方針

- 既存 emulator（cpu/ram/uart/bus）はそのまま活かし、runtime が包む。
- `Bus.on_access` は既定 None で、既存の `tracing` / `last_transactions` は不変。
- 既存テスト（Build/Run、hello.asm "Hi"、Program/Sources、Circuit Write/Run Hello、
  step pc 前進、reg view、bus trace）を壊さない。
- `_do_step` / `_do_run` の「プログラム判定」は `runtime.loaded or RAM が非ゼロ` とし、
  RAM を直接ロードする既存テストも通す。

---

## 今回やらないこと

- Canvas 接続から CPU/RAM/UART を厳密に自動解決する Build Graph 本実装
- 未接続パーツでの実行禁止 / RAM selftest / Fibonacci / ROM イメージ生成
- FPGA 実機書き込み / C コンパイラ / HDL 合成
- breakpoints 本実装 / source-level debugging / disassembler 本格実装
- 複数 CPU 対応 / 内蔵コードエディタ / `ui/canvas.py` 分割
- PHASE COMPLETE / commit / push

---

## 次パッチ候補（記録）

- `PATCH_CIRCUIT_CONNECTIVITY_REQUIRED_V05` — Canvas 配線から実行構成を解決し、未接続実行を禁止
- `PATCH_CPU_RAM_VALIDATION_V05` — CPU/RAM/UART の接続妥当性チェック
- `PATCH_BUILD_GRAPH_PROTOTYPE_V05` — Build Graph 試作（接続→仮想回路構築）
