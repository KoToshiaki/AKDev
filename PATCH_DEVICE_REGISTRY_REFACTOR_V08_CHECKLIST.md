# PATCH_DEVICE_REGISTRY_REFACTOR_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_DEVICE_REGISTRY_REFACTOR_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_BUS_PROTOCOL_VALIDATION_V08` が完了・コミット済みであることを確認
* [ ] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` / `PATCH_PORT_SCHEMA_V08` が完了・コミット済み
* [ ] `core/circuit.py` の `build_address_map` / `validate_address_map` / `format_address_map_summary` を確認
* [ ] `ui/win.py:_make_sim()` の現状（単一 RAM/UART・sim_ram/sim_uart/sim_cpu・runtime_id・UART 窓）を確認
* [ ] `resolve_circuit()` の現状（category 依存の `_is_ram`/`_is_uart`/`_is_cpu`・`target_cpu` キー）を確認
* [ ] `core/ports.py`（`base_port_type`/`normalize_part`）と part.json v2 を確認
* [ ] 既存 `tests/test_address_map_v07.py` / `test_plan_driven_devices_v07.py` / `test_cpu_ram_validation_v07.py` / `test_target_cpu_selection_v07.py` / `test_bus_protocol_validation_v08.py` を確認（全等価アサート有無）

## 1. 設計

* [ ] device spec 構造の確定（node_id/part_id/category/kind/role/addressable/runtime_backed/runtime_id/base/size/end/attach_ranges/reserved/overlay/part）
* [ ] device 分類方針の確定（**part_id ベース**の `device_kind`・category フォールバック）
* [ ] RAM/UART/CPU 互換方針の確定（runtime_id 維持・base/size/UART 窓維持）
* [ ] Address Map 生成方針の確定（`build_address_map_from_devices` 追加・`build_address_map` は委譲）
* [ ] `_make_sim()` refactor 方針の確定（`_resolve_device_specs` / `_build_runtime_devices` 分割・挙動不変）
* [ ] `resolve_circuit()` を今回どこまで触るか確定（**触らない**・VRAM 誤認本修正は次段）
* [ ] legacy mode 互換方針の確定（256B RAM + UART 0x0100 を同じ spec 構造で）
* [ ] VRAM≠RAM を spec 層（part_id kind）で保証する方針の確認

## 2. 実装予定（今回は未実装）

* [ ] `core/devices.py` 新規（device spec 定義 + `device_kind(part)` + `build_device_specs(nodes, plan=)`）
* [ ] RAM/UART/CPU の spec 化（他 kind は spec 化のみ・runtime 生成しない）
* [ ] `core/circuit.py` に `build_address_map_from_devices(mode, device_specs)` 追加、`build_address_map` は委譲
* [ ] `ui/win.py:_make_sim()` を `_resolve_device_specs` / `_build_runtime_devices` に分割（挙動不変）
* [ ] 既存 runtime_id（sim_ram/sim_uart/sim_cpu）・`self._sim_*` 属性互換
* [ ] `mem.vram` を RAM spec / RAM runtime として扱わない判定（spec 層）
* [ ] v07/v08 挙動維持
* [ ] tests 追加

## 3. テスト予定（今回は未追加）

* [ ] device spec 生成（CPU/RAM/UART の kind/role/addressable/runtime_backed/base/size）
* [ ] `device_kind`: ram/vram/uart/cpu/unsupported の分類
* [ ] **`mem.vram` が RAM spec/RAM runtime として扱われない**
* [ ] Address Map: `build_address_map_from_devices` が既存 `build_address_map` と一致
* [ ] `format_address_map_summary` 出力が既存と一致
* [ ] UART 窓 `0x0100–0x0107` 維持・RAM attach が窓を避ける・RAM 64KB/256B
* [ ] runtime 互換（`self._sim_ram`/`_sim_uart`/`_sim_cpu`・runtime_id 不変）
* [ ] legacy mode 維持
* [ ] 既存 v07/v08（plan-driven / address map / cpu-ram / target cpu / bus / port schema / port validation）が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: CPU+RAM+UART で Write→Run が従来どおり（UART 出力・Address Map 表示）
* [ ] 既存 project（system.json）round-trip が不変

## 5. 完了条件

* [ ] 内部が device spec / list driven に寄っている（specs → runtime / Address Map）
* [ ] 既存 RAM/UART/CPU 挙動が維持されている（runtime_id・UART 窓・RAM サイズ）
* [ ] Address Map 結果が既存互換（summary・attach_ranges・MMIO 窓）
* [ ] `mem.vram` を RAM として扱わない土台ができている（device_kind=vram）
* [ ] `resolve_circuit()` を壊していない（target CPU selection 互換）
* [ ] 次の `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` へ進める土台ができている
