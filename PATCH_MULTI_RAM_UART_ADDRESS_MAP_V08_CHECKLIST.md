# PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_DEVICE_REGISTRY_REFACTOR_V08` が完了・コミット済みであることを確認
* [ ] `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` / `PATCH_PORT_SCHEMA_V08` 完了・コミット済み
* [ ] `core/circuit.py:build_address_map_from_devices` の複数 MMIO 窓カービングを確認
* [ ] `core/devices.py` の device spec（kind/role/addressable/runtime_backed/base/size）を確認
* [ ] `core/circuit.py:resolve_circuit` の現状（`_is_cpu`/`_is_ram`/`_is_uart` の category 依存・`target_cpu`）を確認
* [ ] `core/runtime.py:VirtualCircuitRuntime` が単一 cpu/ram/uart を wrap している点を確認
* [ ] `ui/win.py:_resolve_device_specs` / `_build_runtime_devices` の現状を確認
* [ ] 既存 `tests/test_address_map_v07.py`（dict 等価アサート）/ target cpu / bus / device registry を確認

## 1. 設計

* [ ] 複数 RAM 方針確定（1 個目互換・2 個目以降は warning・runtime 化しない・16bit 制約明記）
* [ ] 複数 UART/MMIO 方針確定（1 個目 0x0100・2 個目以降 0x0110+n*0x10・8B・16byte アライン）
* [ ] Address Map 自動配置ルール確定（base 自動割当・複数窓カービング・overlap warning）
* [ ] runtime 生成範囲確定（**案 A: 1 個目互換のみ** / 案 B: 複数 UART runtime のいずれか）
* [ ] `resolve_circuit` 分類修正方針確定（`device_kind` ベース・VRAM 除外・既存キー互換）
* [ ] bus validation / 到達性との関係確定（診断土台のみ・本対応は次段）
* [ ] UI 表示方針確定（Address Map summary 複数行・Log 自動配置結果・Editor は作らない）
* [ ] legacy 互換方針確定（単一 RAM/UART の Address Map dict 完全一致）

## 2. 実装予定（今回は未実装）

* [ ] `resolve_circuit` の `_is_cpu`/`_is_ram`/`_is_uart` を `device_kind` ベースへ（VRAM 除外）
* [ ] device spec の複数 device 対応（rams/uarts を複数 spec 化）
* [ ] 複数 UART/MMIO の base 自動割当ヘルパ（`assign_mmio_bases` 等）
* [ ] Address Map の複数 MMIO 窓カービング（`build_address_map_from_devices` 検証 + 必要なら拡張）
* [ ] 複数 RAM 検出 + warning（runtime 化しない）
* [ ] 既存単一 RAM/UART 完全互換（Address Map dict・runtime・属性）
* [ ] runtime 生成（案 A: 1 個目互換 / 案 B: 複数 UART runtime）
* [ ] UI 表示（Address Map summary 複数行・Log）
* [ ] tests 追加

## 3. テスト予定（今回は未追加）

* [ ] `mem.vram` が `plan["rams"]` に入らない
* [ ] `device_kind` ベースで cpu/ram/uart 分類
* [ ] 複数 RAM 検出（warning / 配置対象外）
* [ ] 複数 UART 検出
* [ ] 既存単一 RAM/UART の Address Map dict が完全一致（回帰）
* [ ] 2 個目 UART が `0x0110–0x0117` に配置される
* [ ] 複数 MMIO 窓で RAM `attach_ranges` が昇順に正しく分割
* [ ] overlap 検出（`validate_address_map` / 自動配置 warning）
* [ ] target CPU selection（v07）が壊れない
* [ ] bus validation（v08）/ device registry（v08）が壊れない
* [ ] legacy mode が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: 複数 UART 配置・Address Map summary 表示・複数 RAM warning
* [ ] 既存 project（system.json）round-trip が不変（単一構成）

## 5. 完了条件

* [ ] 複数 RAM/UART を Address Map 上で扱える（複数 UART 配置・複数 RAM 検出/warning）
* [ ] 単一 RAM/UART 既存挙動が維持されている（dict 完全一致・runtime・属性・UART 窓）
* [ ] `mem.vram` を RAM として扱わない（resolve_circuit device_kind 化）
* [ ] 複数 MMIO 窓で RAM `attach_ranges` が正しく分割される
* [ ] target CPU selection / bus validation / device registry が壊れていない
* [ ] 次の `PATCH_ADDRESS_MAP_EDITOR_V08` / `PATCH_CODE_REGION_MMIO_RELOCATION_V08` へ進める土台ができている
