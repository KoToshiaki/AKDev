# PATCH_ADDRESS_MAP_EDITOR_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_ADDRESS_MAP_EDITOR_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **988 passed**）
* [x] `PATCH_CODE_REGION_MMIO_RELOCATION_V08` が完了・コミット済み（`c6e183e`）
* [x] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` / bus・port・schema 完了・コミット済み
* [x] `core/devices.py` の `MemoryLayout` / `get_memory_layout` / `make_device_spec` / `assign_mmio_bases` を確認
* [x] `core/circuit.py:build_address_map_from_devices`（layout aware・`mmio_inside_ram`）/ `validate_address_map` を確認
* [x] project 保存/読込（`_persist_system` / `_open_project` / `save_system`）を確認
* [x] Run Status Panel / Debug リボンの dock 作法（toggleViewAction・tabify）を確認
* [x] `ui/win.py:_make_sim` / `_resolve_device_specs` / `_build_runtime_devices` を確認

## 1. 設計

* [x] UI 配置方針確定（右側 Dock の Address Map Editor パネル・Port Detail とタブ化）
* [x] 表示項目確定（node/part/kind/role/mode/base/size/end/runtime/overlay/status）
* [x] 編集項目確定（mode auto⇔manual / base / size。read-only: node/part/kind/role/runtime/overlay）
* [x] override 保存方針確定（`address_map_overrides`・node_id キー・mode auto/manual・MainWin state + system.json）
* [x] MemoryLayout との関係確定（layout=auto 既定 / override=manual 上書き・layout 切替 UI は次段）
* [x] validation 方針確定（範囲外/size0/overlap=error・align/UART size/多 RAM=warning・`validate_address_map` 活用）
* [x] Apply/Reset 方針確定（Apply で再構築・error は Apply 不可・Reset to Auto・Refresh）
* [x] 既存互換方針確定（override 無し=現行完全一致・古い project 可・Editor 非起動時は不変）

## 2. 実装

* [x] `ui/address_map_editor.py` 新規（`AddressMapEditor(QDockWidget)` + QTableWidget + Apply/Reset/Refresh）
* [x] device 一覧表示（addressable specs・auto/manual・base/size/end/status）
* [x] base/size 編集（hex/dec parse）+ auto/manual + Reset to Auto + 即時 validation preview
* [x] `core/devices.py` に `apply_address_overrides(specs, overrides)` + `parse_address_int(text)`（純粋関数）
* [x] `core/circuit.py` に `validate_address_overrides(base_specs, overrides, *, layout=)` + issue code 定数
* [x] `ui/win.py` を `_auto_device_specs`（override 無し）+ `_resolve_device_specs`（override 適用）に分割
* [x] Apply 時 `_rebuild_devices()`（`_make_sim` 再構築）+ Run Status/Port Detail 更新 + persist
* [x] project 保存/読込（`_persist_system` に `address_map_overrides` / `_open_project`・`_new_project` で復元・初期化）
* [x] Debug リボンに `toggleViewAction()` 追加
* [x] tests 追加

## 3. テスト（`tests/test_address_map_editor_v08.py` — 23 件）

* [x] `parse_address_int`（0x/decimal/int・不正で ValueError）
* [x] `apply_address_overrides`（no-op / base / size / auto 無視 / 非破壊 / address map 一致）
* [x] `validate_address_overrides`（clean / base<0 / size0 / end>0xFFFF / overlay 許容 / 非 overlay overlap / align・size warning）
* [x] override 無しで Address Map dict 完全一致（回帰）
* [x] Editor 存在・表 populate（addressable のみ）
* [x] Apply で override 反映（UART 再配置・RAM carving）・Reset to Auto で復帰
* [x] 表編集 → collect → Apply / invalid（end>0xFFFF）で Apply ブロック（`has_errors`/ボタン無効）
* [x] override 永続化 round-trip（system.json）
* [x] Hello World / ram_selftest / legacy mode が壊れない

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **1011 passed**（988 + 23）
* [ ] GUI 目視: Editor 起動・base/size 編集・overlap warning/error・Reset・summary 更新（ヘッドレスのため未実施）
* [x] 既存 project（system.json）round-trip 不変（override 無し時・既存テスト通過）

## 5. 完了条件

* [x] Address Map を GUI で確認できる（Dock + 表）
* [x] base/size を安全に編集できる（auto/manual・Reset to Auto・hex/dec parse）
* [x] validation（warning/error）が出る・error は Apply をブロック
* [x] Apply / Reset / Refresh ができ runtime / Address Map summary に反映される
* [x] override 無しで既存挙動が完全維持される（dict 一致・Hello World・selftest・legacy）
* [x] 次の `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` へ進める土台ができている
