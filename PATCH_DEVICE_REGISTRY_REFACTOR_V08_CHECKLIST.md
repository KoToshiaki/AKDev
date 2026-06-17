# PATCH_DEVICE_REGISTRY_REFACTOR_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_DEVICE_REGISTRY_REFACTOR_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **937 passed**）
* [x] `PATCH_BUS_PROTOCOL_VALIDATION_V08` が完了・コミット済み（`2a60232`）
* [x] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（`9b0a589`）/ `PATCH_PORT_SCHEMA_V08`（`a3050a3`）完了・コミット済み
* [x] `core/circuit.py` の `build_address_map` / `validate_address_map` / `format_address_map_summary` を確認
* [x] `ui/win.py:_make_sim()` の現状（単一 RAM/UART・sim_ram/sim_uart/sim_cpu・runtime_id・UART 窓）を確認
* [x] `resolve_circuit()` の現状（category 依存の `_is_ram`/`_is_uart`/`_is_cpu`・`target_cpu` キー）を確認
* [x] `core/ports.py` と part.json v2 を確認
* [x] 既存 v07/v08 テストを確認（address map は dict 等価アサートあり → from_devices で完全一致を担保）

## 1. 設計

* [x] device spec 構造の確定（node_id/part_id/category/kind/role/addressable/runtime_backed/runtime_id/base/size/end/attach_ranges/reserved/overlay/part）
* [x] device 分類方針の確定（**part_id ベース**の `device_kind`・cpu のみ category フォールバック）
* [x] RAM/UART/CPU 互換方針の確定（runtime_id 維持・base/size/UART 窓維持）
* [x] Address Map 生成方針の確定（`build_address_map_from_devices` 追加・`build_address_map` は委譲）
* [x] `_make_sim()` refactor 方針の確定（`_resolve_device_specs` / `_build_runtime_devices` 分割・挙動不変）
* [x] `resolve_circuit()` を今回どこまで触るか確定（**触らない**・VRAM 誤認本修正は次段）
* [x] legacy mode 互換方針の確定（256B RAM + UART 0x0100 を同じ spec 構造で）
* [x] VRAM≠RAM を spec 層（part_id kind）で保証する方針の確認

## 2. 実装

* [x] `core/devices.py` 新規（spec 構造 + `device_kind`/`device_role`/`is_addressable_kind`/`is_runtime_backed_kind`/`make_device_spec`/`synthetic_spec`/`legacy_device_specs`/`build_device_specs` + 定数）
* [x] RAM/UART/CPU の spec 化（他 kind は spec 化のみ・runtime 生成しない）
* [x] `core/circuit.py` に `build_address_map_from_devices(mode, device_specs)` 追加、`build_address_map` は委譲
* [x] `ui/win.py:_make_sim()` を `_resolve_device_specs` / `_build_runtime_devices` に分割（挙動不変）
* [x] メモリマップ定数を `core/devices.py` に単一化し `ui/win.py` は import（`_SIM_*`/`_CIRCUIT_RAM_SIZE` は再エクスポート）
* [x] 既存 runtime_id（sim_ram/sim_uart/sim_cpu）・`self._sim_*` 属性互換
* [x] `mem.vram` を RAM spec / RAM runtime として扱わない判定（spec 層）
* [x] v07/v08 挙動維持
* [x] tests 追加

## 3. テスト（`tests/test_device_registry_refactor_v08.py` — 20 件）

* [x] `device_kind`: cpu/ram/vram/uart/gpio/timer/video/bridge/fpga/unsupported/None
* [x] **`mem.vram` が ram にならない**
* [x] spec: RAM/UART addressable+runtime_backed / CPU addressable=False / **VRAM addressable+runtime_backed=False** / unsupported
* [x] ヘルパ（device_role / is_addressable_kind / is_runtime_backed_kind）・build_device_specs / legacy_device_specs
* [x] Address Map: `build_address_map_from_devices` == 既存 `build_address_map`（circuit / legacy で dict 完全一致）
* [x] UART 窓 `0x0100–0x0107`・RAM attach 窓回避・`validate_address_map` OK・summary 一致
* [x] MainWin: circuit で runtime devices 生成・`self._sim_*`/`_sim_*_node`/runtime_id 維持・Address Map 不変
* [x] Write→Run Hello World / ram_selftest PASS / legacy mode 維持
* [x] **`mem.vram` を RAM node に配線しても spec 層で ram にならない**（runtime_backed=False）
* [x] 既存 v07/v08 が無改変で通過

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **957 passed**（937 + 20）
* [ ] GUI 目視: CPU+RAM+UART で Write→Run が従来どおり（ヘッドレスのため未実施）
* [x] 既存 project（system.json）round-trip 不変（既存テスト通過で実証・system.json 差分なし）

## 5. 完了条件

* [x] 内部が device spec / list driven に寄っている（specs → runtime / Address Map）
* [x] 既存 RAM/UART/CPU 挙動が維持されている（runtime_id・UART 窓・RAM サイズ）
* [x] Address Map 結果が既存互換（summary・attach_ranges・MMIO 窓・dict 完全一致）
* [x] `mem.vram` を RAM として扱わない土台ができている（device_kind=vram / runtime_backed=False）
* [x] `resolve_circuit()` を壊していない（target CPU selection 互換・無改変）
* [x] 次の `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` へ進める土台ができている
