# PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の **5 番目の候補パッチ**の設計資料。
> 本書は設計のみ。**実装・テスト追加・part.json 変更・挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: `PATCH_PORT_SCHEMA_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` /
> `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` 完了
> （`pytest tests/` 957 passed）。

---

## 1. 目的

- `PATCH_DEVICE_REGISTRY_REFACTOR_V08` の device spec / list driven 構造を **N device 対応**へ進める。
- 複数 RAM / 複数 UART / 複数 MMIO device を **Address Map 上で共存・診断**できるようにする。
- Address Map の `attach_ranges` / `reserved` / `overlay` を **複数 MMIO 窓**対応にする。
- `resolve_circuit()` の RAM/UART/CPU 分類を **category 依存から `device_kind`（part_id）ベース**へ移し、
  **`mem.vram` を `rams` に拾わない**ようにする（VRAM 誤認の本修正）。
- target CPU から見た device 到達性の**診断土台**を作る。
- ただし **Address Map Editor / GUI 編集 / MMIO 再配置 / 新デバイス runtime は今回やらない**。既存単一
  RAM/UART 挙動は完全互換。

### スコープ（明確化）

「**複数 device の検出・分類（part_id ベース）・Address Map への配置（複数 MMIO 窓カービング）・診断
（warning）**」まで。AK32 の 16bit（64KB）制約上、**複数 RAM の真の共存は本パッチでは扱わず**
（検出 + warning に留める）、複数 UART/MMIO 窓の Address Map 配置を主対象とする。RAM 縮小・領域再配置は
`PATCH_CODE_REGION_MMIO_RELOCATION_V08` へ送る。

---

## 2. 現在の問題

- `PATCH_DEVICE_REGISTRY_REFACTOR_V08` で device spec / list driven の土台はできたが、**runtime 生成は
  実質 1 個目の RAM/UART** に留まる。
- `build_address_map_from_devices()` は 1 memory + 1 mmio 窓の汎用化までで、**複数 MMIO 窓の配置ルールは
  未確定**。
- 複数 RAM/UART がある場合の **base/size 割り当てルールがない**。
- **`resolve_circuit()` は依然 category 依存**（`_is_ram` = category "mem"）。`mem.vram` を `rams` に拾う。
- bus group validation はあるが、**Address Map device と bus 到達性の突き合わせは未実装**。
- Address Map Editor が無いため、当面は**自動配置ルール**が必要。
- **16bit アドレス制約**: AK32 の `LDI`/`JMP` は imm16（最大 `0xFFFF`）。既存 RAM は 64KB 全域を占有する
  ため、複数 RAM を素直に並べる空きがない（要・RAM 縮小 or 再配置 = 次段）。

---

## 3. 対応方針の大枠

- 既存の**単一 RAM/UART 構成は完全互換**（Address Map dict・runtime・UART 窓 `0x0100–0x0107`・RAM 64KB /
  legacy 256B）。
- 複数 device はまず**自動配置**で扱う（GUI 編集は次段）。
- **runtime 化は RAM/UART 中心**。複数 UART runtime は段階導入（§7 で 2 案提示）。複数 RAM runtime は
  16bit 制約のため**本パッチでは行わず検出 + warning**。
- ROM/VRAM/Input/Storage runtime は今回**実装しない**（spec 分類のみ・`PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`）。
- 既存テストを壊さない（単一構成の Address Map dict 完全一致を維持）。

---

## 4. 複数 RAM の扱い

- **1 個目の RAM**: 既存互換で `0x0000–0xFFFF`（circuit）/ `0x0000–0x00FF`（legacy）。runtime 化（sim_ram）。
- **2 個目以降の RAM**:
  - 16bit/64KB 制約上、1 個目が全域を占有するため**素直に並べられない**。
  - 本パッチでは **runtime 化しない** + **warning**（例 `MULTI_RAM_UNSUPPORTED` / Address Map issue）。
  - 真の共存（RAM 縮小・領域分割・base 自動割当）は **`PATCH_CODE_REGION_MMIO_RELOCATION_V08`** /
    `PATCH_ADDRESS_MAP_EDITOR_V08` へ送る。
- 設計記録: 「複数 RAM = 検出 + Address Map 診断 + warning まで」。AK32 が imm16 アドレスである点を明記。

---

## 5. 複数 UART / MMIO device の扱い

- **1 個目の UART**: 既存どおり `0x0100–0x0107`（8B）。
- **2 個目以降の UART/MMIO**: **16byte アライン**で自動配置（例 `0x0110`, `0x0120`, `0x0130` …）。size 8B。
  - 配置式（案）: `base = FIRST_UART_BASE + n * 0x10`（n=1,2,…）。各窓は RAM 内 → `reserved` でくり抜く。
- **複数 MMIO 窓**を昇順に並べ、RAM の `attach_ranges` を**複数分割**で生成（§6）。
- gpio/timer/video_regs などの将来 MMIO device: spec は分類するが、**今回 runtime 化しない**。
  Address Map に載せるかは選択制（推奨: 接続済み & runtime 化対象のみ載せ、未対応 kind は載せず info）。
- 複数 UART **runtime** を今回生成するかは §7 の判断による（推奨は 1 個目互換 + Address Map のみ先行）。

---

## 6. Address Map 自動配置ルール

- **RAM**:
  - 1 個目 = `0x0000–0xFFFF`（circuit）。複数 RAM は warning・配置対象外（§4）。
- **UART / MMIO**:
  - 1 個目 UART = `0x0100–0x0107`。2 個目以降 = `0x0110 + (n-1)*0x10`、size 8B、16byte アライン。
  - base 未指定の addressable spec に対して**自動割当**（既に base を持つ spec はそれを尊重）。
- **MMIO window carving**:
  - memory device（RAM）の内側に入る各 MMIO 窓を `reserved` に集約し、**昇順整列**して RAM の
    `attach_ranges` を分割（`build_address_map_from_devices` は既に複数窓カービングに対応済み＝この一般化を活用）。
  - 各 MMIO device は `role="mmio"` / `overlay="ram"`。
- **overlap**:
  - 既存 `validate_address_map()`（attach_ranges 同士）を活用。
  - 自動配置で overlap が出たら warning / validation issue（例 `ADDRESS_AUTO_PLACE_OVERLAP`）。
- 既存単一 RAM+UART の出力は**完全一致**を維持（回帰テストで担保）。

---

## 7. runtime 生成方針

2 案を提示し、**案 A（保守的）を推奨**:

- **案 A（推奨・behavior-first）**: runtime は **1 個目 RAM + 1 個目 UART + CPU** のみ（現状維持）。
  Address Map だけ N device 対応にする。複数 UART/RAM は spec/Address Map で**検出・診断**するが
  runtime 化しない。`self._sim_ram` / `_sim_uart` / `_sim_cpu` は不変。最小リスク。
- **案 B（段階・複数 UART runtime）**: Address Map の各 UART 窓に `UartPart` を生成して attach。
  1 個目は `self._sim_uart`（互換）、追加分は `self._sim_uarts`（list 属性）に保持。
  `VirtualCircuitRuntime`・UART Console・Bus Trace は 1 個目を主表示（追加 UART は bus 経由で動くが
  Console 表示は次段）。複数 RAM runtime は 16bit 制約で**行わない**。

共通方針:
- 既存属性 `self._sim_ram` / `_sim_uart` / `_sim_cpu` / `_sim_*_node` は**1 個目を保持**（互換）。
- 追加 device を持つ場合のみ `self._sim_rams` / `self._sim_uarts`（list）を**任意追加**（1 個目も含む）。
- `VirtualCircuitRuntime` は当面単一 cpu/ram/uart を wrap（複数対応は将来）。

> 推奨: 本パッチは **案 A（runtime は 1 個目互換、Address Map のみ N device）**。複数 UART runtime（案 B）は
> 必要が出た時点で別パッチ化。これにより既存 Bus Trace/UART Console/Runtime を一切触らず安全。

---

## 8. `resolve_circuit()` の分類修正方針

- `core/circuit.py` の `_is_cpu` / `_is_ram` / `_is_uart` を **`core.devices.device_kind(part)` ベース**へ移行:
  - `_is_cpu`  → `device_kind == "cpu"`
  - `_is_ram`  → `device_kind == "ram"`（**`mem.vram` は除外される**）
  - `_is_uart` → `device_kind == "uart"`
- これにより **`mem.vram` を `rams` に拾わない**（VRAM 誤認の本修正）。
- 既存キー `plan["cpu"]` / `plan["rams"]` / `plan["uarts"]` / `plan["target_cpu"]` / `cpu_present` は**互換維持**。
- 追加（任意）: `plan["devices"]`（全 device spec）/ `plan["addressable_devices"]` を新キーで足す案
  （既存キーは壊さない）。
- node 入力に `part`（part dict）を渡せるよう `_resolve_circuit_plan()`（ui/win.py）を拡張
  （現在 node は `{node_id, category, part_id, name}`。`device_kind` は part_id で判定できるので
  既存の `part_id` で足りる → **node 構造変更は最小 or 不要**）。
- target CPU selection（`target_cpu_id`）の挙動は不変。
- 移行手順: 分類関数差し替え → 既存 v07/v08 テスト（target cpu / address map / plan-driven）が緑であることを
  逐次確認。`mem.vram` を含むテストを追加。

> 重要: `device_kind` は part_id ベース。resolve_circuit が受け取る node には既に `part_id` がある
> （`_resolve_circuit_plan` が供給）。よって part dict 全体を渡さずとも `device_kind({"id": part_id})` 相当で
> 判定できる（実装時に `device_kind` を part_id 受け取り可能にするか、ヘルパを用意）。

---

## 9. bus validation / 到達性との関係

- device spec に **所属 bus group** を持たせるかは任意（`build_bus_groups` の結果と node_id で突き合わせ可能）。
- **target CPU が属する bus group にある addressable device のみ Address Map に載せる**案を検討
  （到達できない孤立 slave を載せない）。本パッチでは**診断土台**まで:
  - target CPU から（bus group 上で）到達できない addressable device → warning（例 `DEVICE_UNREACHABLE`）。
- bus bridge 越しの到達性は**今回やらない**（`PATCH_BUS_PROTOCOL_VALIDATION` の bridge 同様、次段）。
- 複数 master がある場合は既存 `BUS_MULTIPLE_MASTERS`（bus_validation）に委ねる。
- 推奨: 到達性は**本対応せず**、`validate_bus_protocol` と Address Map を**併記表示**するに留める
  （突き合わせ本実装は次段）。

---

## 10. UI / Debug 表示方針

- **Address Map summary**（`format_address_map_summary`）: 複数 RAM/UART を各行で列挙（既存フォーマット踏襲・
  device ごとに 1 行）。複数 UART は `UART node 0x0110-0x0117 8B MMIO` のように追加表示。
- **Run Status Panel**: device 数 summary（例 `RAM:1 UART:2`）を任意追加（最小）。
- **Port Detail**: 既存の port/bus validation issue に加え、Address Map 自動配置の warning を表示しても良い
  （合算）。
- **Log**: 自動配置結果（2 個目 UART の base 等）と warning を出す。
- **Address Map Editor / base-size GUI 編集は作らない**（次段 `PATCH_ADDRESS_MAP_EDITOR_V08`）。

---

## 11. 実装スコープ案（今回は設計のみ）

推奨スコープ（実装する場合）:
- `core/circuit.py:resolve_circuit` の `_is_*` を `device_kind` ベースへ（VRAM 除外）。`rams`/`uarts` は
  接続済み device を**複数**返す（既に list だが 1 個前提の利用箇所を確認）。
- `core/devices.py` に **複数 UART/MMIO の base 自動割当**ヘルパ（`assign_mmio_bases(specs)` 等）を追加。
- `build_address_map_from_devices` の複数 MMIO 窓カービングを**テストで明示**（既に対応済みなので主に検証）。
- `ui/win.py:_resolve_device_specs` で複数 RAM/UART を spec 化（runtime 化は **案 A=1 個目のみ**）。
- 複数 RAM は warning、複数 UART は Address Map に配置（runtime 化は段階判断）。
- 既存単一構成は完全互換。新規テスト追加。

やらないこと: Address Map Editor、GUI 編集、MMIO 再配置、新デバイス runtime、複数 RAM の真の共存。

---

## 12. テスト方針（実装時に追加するテスト）

- `mem.vram` が `plan["rams"]` に入らない（resolve_circuit device_kind 化）。
- `device_kind` ベースで cpu/ram/uart が正しく分類される。
- 複数 RAM を検出できる（warning / 配置対象外）。
- 複数 UART を検出できる。
- 既存単一 RAM/UART の Address Map dict が**完全一致**（回帰）。
- 2 個目 UART が `0x0110–0x0117` に配置される（自動割当）。
- 複数 MMIO 窓で RAM `attach_ranges` が昇順に正しく分割される。
- overlap が検出される（`validate_address_map` / 自動配置 warning）。
- target CPU selection（v07）が壊れない。
- bus validation（v08）/ device registry（v08）が壊れない。
- legacy mode が壊れない。
- `python -m pytest tests/` 全通過。

---

## 13. 今回やらないこと

- Address Map Editor
- GUI 上の base/size 編集
- MMIO 再配置 UI / コード領域拡張
- ROM / VRAM / Input / Storage / Video runtime
- CPU 命令拡張
- bus bridge 完全 routing
- 複数 RAM の真の共存（runtime 化）
- HDL / FPGA export
- コード実装 / テスト追加 / part.json 変更
- commit / push

---

## 14. 次に続くパッチ（候補順）

1. `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`（本パッチ — 複数 device 検出・Address Map 配置・resolve_circuit kind 化）
2. `PATCH_ADDRESS_MAP_EDITOR_V08`（base/size の GUI 編集・自動配置の上書き）
3. `PATCH_CODE_REGION_MMIO_RELOCATION_V08`（RAM サイズ可変・コード領域拡張・MMIO 再配置 → 複数 RAM 共存）
4. `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`（ROM / Input などの runtime 追加）
5. `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（CALL / RET / IN・スタック）

> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / opcode 単一化 /
> テストフィクスチャ整理。
