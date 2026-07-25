# PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **957 passed**）
* [x] `PATCH_DEVICE_REGISTRY_REFACTOR_V08` が完了・コミット済み（`ffa75f9`）
* [x] `PATCH_BUS_PROTOCOL_VALIDATION_V08`（`2a60232`）/ `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（`9b0a589`）/ `PATCH_PORT_SCHEMA_V08`（`a3050a3`）完了・コミット済み
* [x] `core/circuit.py:build_address_map_from_devices` の複数 MMIO 窓カービングを確認（既に複数窓対応）
* [x] `core/devices.py` の device spec を確認
* [x] `core/circuit.py:resolve_circuit` の現状（`_is_*` の category 依存・`target_cpu`）を確認
* [x] `core/runtime.py:VirtualCircuitRuntime` が単一 cpu/ram/uart を wrap している点を確認
* [x] `ui/win.py:_resolve_device_specs` / `_build_runtime_devices` の現状を確認
* [x] 既存テストを確認（`basic_ram` は bare Canvas overlay のみで resolve 非経由 → kind 化で安全）

## 1. 設計

* [x] 複数 RAM 方針確定（1 個目互換・2 個目以降 warning・runtime 化しない・16bit 制約明記）
* [x] 複数 UART/MMIO 方針確定（1 個目 0x0100・2 個目以降 0x0110+n*0x10・8B・16byte アライン）
* [x] Address Map 自動配置ルール確定（`assign_mmio_bases` で base 自動割当・複数窓カービング）
* [x] runtime 生成範囲確定（**案 A: 1 個目互換のみ**。追加 UART は Address Map 配置のみ）
* [x] `resolve_circuit` 分類修正方針確定（`device_kind` ベース・VRAM 除外・既存キー互換・rams/uarts を node_id ソートで決定的に）
* [x] bus validation / 到達性との関係確定（本パッチでは結びつけず・診断土台は次段）
* [x] UI 表示方針確定（Address Map summary 複数行・Log に MULTI_RAM warning・Editor は作らない）
* [x] legacy 互換方針確定（単一 RAM/UART の Address Map dict 完全一致）

## 2. 実装

* [x] `resolve_circuit` の `_is_cpu`/`_is_ram`/`_is_uart` を `device_kind` ベースへ（`_node_kind` 経由・VRAM 除外）
* [x] `resolve_circuit` の rams/uarts を node_id ソートで決定的に（earliest-placed = primary）
* [x] `core/devices.py` に `assign_mmio_bases(specs)`（複数 UART/MMIO base 自動割当）追加
* [x] `core/devices.py` に `multi_device_warnings(specs)`（`MULTI_RAM_UNSUPPORTED`）追加
* [x] Address Map の複数 MMIO 窓カービング（`build_address_map_from_devices` は既に対応・検証）
* [x] `ui/win.py:_resolve_device_specs` で全 RAM/UART を spec 化 + `assign_mmio_bases`
* [x] `ui/win.py:_build_runtime_devices` で 1 個目 RAM/UART/CPU のみ runtime 化・2 個目以降 RAM は Address Map 非掲載・multi-RAM warning を Log
* [x] 既存単一 RAM/UART 完全互換（Address Map dict・runtime_id・`self._sim_*`/`_sim_*_node`・UART 窓）
* [x] tests 追加

## 3. テスト（`tests/test_multi_ram_uart_address_map_v08.py` — 16 件）

* [x] `mem.vram` が `plan["rams"]` に入らない / `mem.ram` は入る / 複数 RAM・UART が列挙される
* [x] `assign_mmio_bases`: 単一 UART 不変 / 複数 UART 0x100・0x110・0x120 / 1 個目のみ runtime_backed / RAM・CPU 不変
* [x] `multi_device_warnings`: 複数 RAM で `MULTI_RAM_UNSUPPORTED` / 単一は無し
* [x] 2 UART 窓で RAM `attach_ranges` 分割 `[(0,0xFF),(0x108,0x10F),(0x118,0xFFFF)]`・valid
* [x] 単一 RAM/UART の Address Map dict が `build_address_map` と完全一致（回帰）
* [x] MainWin: 単一互換+Run / selftest PASS / 2 UART 配置+1 個目 runtime+Run / 複数 RAM warning+1 個目のみ map / VRAM のみ→no RAM block / legacy 維持
* [x] 既存 v07/v08 が無改変で通過（device_registry の VRAM テストのみ新挙動へ更新）

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **973 passed**（957 + 16）
* [ ] GUI 目視: 複数 UART 配置・Address Map summary・複数 RAM warning（ヘッドレスのため未実施）
* [x] 既存 project（system.json）round-trip 不変（既存テスト通過・system.json 差分なし）

## 5. 完了条件

* [x] 複数 RAM/UART を Address Map 上で扱える（複数 UART 配置・複数 RAM 検出/warning）
* [x] 単一 RAM/UART 既存挙動が維持されている（dict 完全一致・runtime・属性・UART 窓）
* [x] `mem.vram` を RAM として扱わない（resolve_circuit device_kind 化）
* [x] 複数 MMIO 窓で RAM `attach_ranges` が正しく分割される
* [x] target CPU selection / bus validation / device registry が壊れていない
* [x] 次の `PATCH_ADDRESS_MAP_EDITOR_V08` / `PATCH_CODE_REGION_MMIO_RELOCATION_V08` へ進める土台ができている
