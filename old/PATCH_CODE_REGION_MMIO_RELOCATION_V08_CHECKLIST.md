# PATCH_CODE_REGION_MMIO_RELOCATION_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_CODE_REGION_MMIO_RELOCATION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **973 passed**）
* [x] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` が完了・コミット済み（`1707734`）
* [x] `PATCH_DEVICE_REGISTRY_REFACTOR_V08`（`ffa75f9`）/ bus・port・schema パッチ完了・コミット済み
* [x] `core/devices.py` の定数と `make_device_spec`/`assign_mmio_bases` を確認
* [x] `core/circuit.py:build_address_map_from_devices` の窓くり抜きを確認
* [x] `ui/win.py:_make_sim` / `_resolve_device_specs` / `_build_runtime_devices` を確認
* [x] `core/cpu.py`（`reset_pc`）/ `asm/asm.py`（imm16・0x0000 開始）/ ローダのコード配置を確認

## 1. 設計

* [x] layout mode 方針確定（`MemoryLayout` dataclass・`legacy`/`circuit_compat`/`game16`）
* [x] 互換 layout 方針確定（既定 = `circuit_compat` = 現行・dict 完全一致）
* [x] RAM サイズ可変方針確定（`ram_base`/`ram_size` を layout 由来へ・既定で現行値）
* [x] MMIO 再配置方針確定（`mmio_base`/`mmio_stride`/`mmio_size`/`mmio_inside_ram`・`assign_mmio_bases` layout aware）
* [x] ROM / code 領域方針確定（`code_base`/`reset_pc`・既定 0x0000・ROM 導入は次段）
* [x] stack / data 領域方針確定（`stack_top` 予約・game16 で 0xBFFF・実装は命令拡張パッチ）
* [x] Address Map Editor との関係確定（layout 先・Editor は上書き・次段）

## 2. 実装

* [x] `core/devices.py` に `MemoryLayout`（frozen dataclass）を追加
* [x] `LEGACY` / `CIRCUIT_COMPAT`（既定）を**現行値**で定義、`GAME16` は design-only 候補で定義（未使用）
* [x] `get_memory_layout(mode)`（None/circuit→circuit_compat / legacy / game16 / 未知→circuit_compat）
* [x] モジュール定数（RAM_BASE 等）を layout から導出（値不変・import 互換）
* [x] `make_device_spec(..., layout=)` / `synthetic_spec` / `legacy_device_specs(layout=)` / `build_device_specs(..., layout=)` を layout aware に
* [x] `assign_mmio_bases(specs, *, layout=)` を layout aware に（既定で 0x0100/0x0110…）
* [x] `build_address_map_from_devices(mode, specs, *, layout=)` を layout aware に（`mmio_inside_ram` で carving 切替・既定一致）
* [x] `build_address_map(...)` 互換ラッパ維持（mode から layout 解決・出力不変）
* [x] `ui/win.py:_make_sim`/`_resolve_device_specs`/`_build_runtime_devices` に layout を通す（既定 circuit_compat / legacy）
* [x] `AK32Part(reset_pc=layout.reset_pc)`（既定 0x0000）
* [x] default 互換テスト追加 / `game16` は定義 + layout aware テストのみ（実行未使用）

## 3. テスト（`tests/test_code_region_mmio_relocation_v08.py` — 15 件）

* [x] `circuit_compat` / `legacy` / `game16` の値・`get_memory_layout`（既定/未知 fallback）・定数一致
* [x] 既定 layout で `make_device_spec` / `assign_mmio_bases` / `build_address_map_from_devices` が現行一致
* [x] `build_address_map` wrapper（circuit/legacy）が不変
* [x] layout aware: game16 で MMIO 0xE000 / `mmio_inside_ram=True` carving / `False` 非 overlap
* [x] MainWin: 既定で Write→Run（Hello World）/ ram_selftest PASS / reset_pc=0x0000 / legacy 維持
* [x] 既存 v07/v08（address map / plan-driven / cpu-ram / target cpu / device registry / multi RAM-UART）不変

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **988 passed**（973 + 15）
* [ ] GUI 目視: 既定で Write→Run が従来どおり（ヘッドレスのため未実施）
* [x] 既存 project（system.json）round-trip 不変（既存テスト通過・system.json 差分なし）

## 5. 完了条件

* [x] layout 設計（`MemoryLayout`）が明確になっている
* [x] 既存互換を維持できる実装範囲が明確（既定 = circuit_compat）
* [x] RAM サイズ可変 / MMIO 再配置の土台（layout 引数の配線）ができている
* [x] 既定で Address Map dict・UART 0x0100・RAM 64KB・Hello World が不変
* [x] 次の `PATCH_ADDRESS_MAP_EDITOR_V08` / `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` へ進める土台ができている
