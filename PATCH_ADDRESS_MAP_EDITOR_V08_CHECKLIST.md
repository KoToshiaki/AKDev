# PATCH_ADDRESS_MAP_EDITOR_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_ADDRESS_MAP_EDITOR_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_CODE_REGION_MMIO_RELOCATION_V08` が完了・コミット済みであることを確認
* [ ] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` / `PATCH_DEVICE_REGISTRY_REFACTOR_V08` / bus・port・schema 完了・コミット済み
* [ ] `core/devices.py` の `MemoryLayout` / `get_memory_layout` / `make_device_spec` / `assign_mmio_bases` を確認
* [ ] `core/circuit.py:build_address_map_from_devices`（layout aware・`mmio_inside_ram`）/ `validate_address_map` を確認
* [ ] project 保存/読込（system.json `{chips,parts,links,memory_map}` / canvas `{parts,connections}` / `_persist_system`）を確認
* [ ] Run Status Panel（`ui/run_status.py` の Address Map summary）/ Debug リボンの dock 作法を確認
* [ ] `ui/win.py:_make_sim` / `_resolve_device_specs` / `_build_runtime_devices` を確認

## 1. 設計

* [ ] UI 配置方針確定（右側 Dock の Address Map Editor パネル推奨 / Dialog 代替）
* [ ] 表示項目確定（node_id/part/kind/role/base/size/end/runtime_backed/overlay/status）
* [ ] 編集項目確定（base / size / auto⇔manual / Reset to Auto。read-only: kind/role/node_id/runtime_id）
* [ ] override 保存方針確定（`address_map_overrides`・node_id キー・mode auto/manual・MainWin state + 任意 system.json）
* [ ] MemoryLayout との関係確定（layout=既定 / override=上書き優先 / layout 切替は表示のみ・次段）
* [ ] validation 方針確定（範囲外/size0/overlap=error・align/UART size/多 RAM=warning・`validate_address_map` 活用）
* [ ] Apply/Cancel 方針確定（Apply で再構築・invalid は Apply 不可・Reset to Auto）
* [ ] 既存互換方針確定（override 無し=現行完全一致・古い project 可・Editor 非起動時は不変）

## 2. 実装予定（今回は未実装）

* [ ] `ui/address_map_editor.py` 新規（Dock + QTableWidget）
* [ ] device 一覧表示（read-only 表示が先）
* [ ] base/size 編集 + auto/manual トグル + Reset to Auto
* [ ] validation preview（`validate_address_map` + Editor チェック・行/ステータス表示）
* [ ] `core/devices.py` に `apply_address_overrides(specs, overrides)`（純粋関数）
* [ ] `ui/win.py` パイプラインに override 適用を挟む（auto→manual・`self._address_overrides`）
* [ ] Apply 時 `_make_sim()` 再構築 + Run Status/summary 更新
* [ ] project 保存/読込（`address_map_overrides`）※最小 or 次段分離
* [ ] Debug リボンに toggleViewAction 追加
* [ ] tests 追加

## 3. テスト予定（今回は未追加）

* [ ] override 無しで既存 Address Map dict 完全一致（回帰）
* [ ] base override が反映される
* [ ] size override が反映される
* [ ] Reset to Auto で自動配置に戻る
* [ ] invalid range（end>0xFFFF / size 0 / base<0）検出
* [ ] overlap（RAM 同士 / 非 overlay RAM-MMIO）を error 検出
* [ ] `mmio_inside_ram=True` の overlay は許容
* [ ] `mmio_inside_ram=False` の overlap は error
* [ ] 古い project（override 無し）を開ける
* [ ] override 付き project の round-trip（永続化実装時）
* [ ] Hello World / ram_selftest が壊れない
* [ ] legacy mode が壊れない
* [ ] 既存 v07/v08（address map / device registry / multi RAM-UART / code region）が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: Editor 起動・base/size 表示編集・overlap warning/error・Reset to Auto・summary 更新
* [ ] 既存 project（system.json）round-trip が不変（override 無し）

## 5. 完了条件

* [ ] Address Map を GUI で確認できる
* [ ] base/size を安全に編集できる（auto/manual・Reset to Auto）
* [ ] validation（warning/error）が出る・error は Apply をブロック
* [ ] Apply / Reset ができ runtime に反映される
* [ ] override 無しで既存挙動が完全維持される（dict 一致・Hello World・legacy）
* [ ] 次の `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` へ進める土台ができている
