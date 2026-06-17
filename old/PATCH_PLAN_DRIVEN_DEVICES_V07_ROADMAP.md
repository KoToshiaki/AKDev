# PATCH_PLAN_DRIVEN_DEVICES_V07 — ROADMAP

> v0.7（Plan-driven Virtual Devices & Address Map）最初のパッチ。
> 親計画: `ROADMAP7.md` / 進捗: `PATCH_PLAN_DRIVEN_DEVICES_V07_CHECKLIST.md`。

---

## 目的

現在の CircuitPlan は接続チェックとログ表示が中心で、実行時の RAM/UART はまだ
固定 runtime 寄り（`_make_sim` が plan を見ずに固定 256B RAM/UART を生成し、
`_runtime.plan = plan` を付与するだけ）。

本パッチで、**Canvas 上で接続された RAM/UART/CPU ノードをもとに実際の仮想デバイスを
生成し、それを runtime の実行デバイスとして使う**構造へ変える。あわせて circuit mode の
RAM サイズを拡張する。

---

## 設計

### アドレス空間の制約（重要）

- AK32 の `LDI rd, imm16` は **imm16（最大 0xFFFF）**。実効アドレス空間は 16bit。
- アセンブラは **load base 0 前提**（`JMP imm16` は絶対アドレス）。よって reset PC / コードは
  0x0000 から。
- UART は既存サンプル（`hello.asm` / `hello_world.asm`）と多数テストで **0x0100 固定**。

→ これらを同時に満たしつつ RAM を拡張するには、**RAM を 64KB（0x0000〜0xFFFF）として
アドレス空間全体に置き、UART を RAM 内の MMIO ウィンドウ（0x0100〜0x0107）として開ける**。
RAM を bus に 2 レンジ（`0x0000–0x00FF` と `0x0108–0xFFFF`）で attach し、その間に UART を置く。
これにより UART は従来どおり 0x0100、コードは 0x0000 から、データは最大 0xFFFF まで使える。
（UART を高位アドレスへ移すとサンプル/テストの 0x0100 と矛盾し imm16 制約とも干渉するため採らない。）

### circuit mode / legacy mode

| モード | 条件 | RAM | UART | 備考 |
|---|---|---|---|---|
| circuit | plan に CPU/接続RAM/接続UART が揃う | **64KB**（MMIO ウィンドウ方式）| 0x0100 | plan のノードに対応する実デバイス |
| legacy | Canvas に CPU なし（plan=None 等）| 256B（従来）| 0x0100 | 完全に従来挙動を維持 |

### `_make_sim(plan)` の変更

- plan が circuit 構成（`plan["cpu"]` かつ `plan["rams"]` かつ `plan["uarts"]`）なら circuit build、
  それ以外は legacy build。
- circuit build: 64KB RamPart を生成し、bus に `0x0000–0x00FF` / `0x0108–0xFFFF` を attach、
  UART を `0x0100–0x0107` に attach。`self._sim_ram` / `self._sim_uart` / `self._sim_cpu` を
  これらにする（既存 UI/テストの参照名を維持）。plan のノード id を
  `self._sim_ram_node` / `self._sim_uart_node` / `self._sim_cpu_node` に保持（後続 Run Status 用）。
- runtime は従来どおり `VirtualCircuitRuntime(bus, ram, uart, cpu)` で包む。
- デバイス id は `sim_ram` / `sim_uart` / `sim_cpu` のまま（bus.last_transactions / signal overlay
  / on_access の UART 判定キーを変えないことでリスク最小化）。

### 影響範囲

- 変更は基本 `_make_sim` に局所化。`write_program` / `_build` / `_do_run` / `_do_step` /
  各パネル更新（`_update_memory_viewer` 等）は `self._sim_ram` 等を参照しているため、
  `_make_sim(plan)` が plan デバイスを割り当てれば自動的に plan デバイスで動く。

---

## 今回やらないこと

- 複数 RAM / 複数 UART の本格対応（先頭 1 個のみ）
- 複数 CPU 同時実行
- Address Map Editor（base/size 管理・表示は PATCH_ADDRESS_MAP_V07）
- VRAM / Video / Storage / Input
- CPU/RAM Validation 本体・Fibonacci（PATCH_CPU_RAM_VALIDATION_V07）
- UI 大改造

---

## テスト（`tests/test_plan_driven_devices_v07.py` 新規）

- plan 由来 RAM が runtime の実行 RAM（`runtime.ram is win._sim_ram`、サイズ拡張）
- plan 由来 UART が runtime の実行 UART（`runtime.uart is win._sim_uart`）
- circuit mode の RAM サイズが拡張（`win._sim_ram.size >= 0x10000`）
- Write Program が接続 RAM へロード（先頭バイト一致）
- Run で接続 UART へ Hello World
- 拡張 RAM の高位アドレス（例 0x2000）へ ST→LD で読み書きできる
- legacy mode（CPU 未配置）Build→Run が従来どおり（UART "Hi"・RAM 256B）
- 未接続 CPU/RAM/UART のブロックが維持される
- Step Trace が壊れていない（Step で trace dict が返る）

既存テストは全件維持（779）。

---

## 互換性

legacy mode / 既存 Build→Run / Hello World / Step Trace / Program/Sources / Wiring /
Visual Port / Wire Style / Save/Load / Hub / 既存テストを壊さない。
