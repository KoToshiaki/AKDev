# PATCH_CODE_REGION_MMIO_RELOCATION_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_CODE_REGION_MMIO_RELOCATION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 変更・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` が完了・コミット済みであることを確認
* [ ] `PATCH_DEVICE_REGISTRY_REFACTOR_V08` / `PATCH_BUS_PROTOCOL_VALIDATION_V08` / `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` / `PATCH_PORT_SCHEMA_V08` 完了・コミット済み
* [ ] `core/devices.py` の定数（RAM_BASE/UART_BASE/UART_SIZE/CIRCUIT_RAM_SIZE/LEGACY_RAM_SIZE）と `make_device_spec`/`assign_mmio_bases` を確認（layout 化候補）
* [ ] `core/circuit.py:build_address_map_from_devices` の窓くり抜き（`mmio_inside_ram` 相当）を確認
* [ ] `ui/win.py:_make_sim` / `_resolve_device_specs` / `_build_runtime_devices` を確認
* [ ] `core/cpu.py`（`reset_pc`）/ `asm/asm.py`（コード配置・imm16）/ ローダ（`_assemble_and_load`）のコード配置を確認

## 1. 設計

* [ ] layout mode 方針確定（`MemoryLayout` 構造・`legacy`/`circuit_compat`/（案）`game16`）
* [ ] 互換 layout 方針確定（既定 = `circuit_compat` = 現行・dict 完全一致）
* [ ] RAM サイズ可変方針確定（`ram_base`/`ram_size` を layout 由来へ・既定で現行値）
* [ ] MMIO 再配置方針確定（`mmio_base`/`mmio_stride`/`mmio_size`/`mmio_inside_ram`・`assign_mmio_bases` を layout aware）
* [ ] ROM / code 領域方針確定（`code_base`/`reset_pc`・既定 0x0000・ROM 導入は次段）
* [ ] stack / data 領域方針確定（`stack_top` 予約・実装は命令拡張パッチ）
* [ ] Address Map Editor との関係確定（layout 先・Editor は上書き・次段）

## 2. 実装予定（今回は未実装）

* [ ] `core/devices.py` に `MemoryLayout` 構造を追加（dict or dataclass）
* [ ] `legacy` / `circuit_compat`（既定）layout を**現行値**で定義（`game16` は定義のみ or 次段）
* [ ] `make_device_spec()` の RAM/UART base/size を layout 由来へ（既定で現行値）
* [ ] `assign_mmio_bases(specs, layout=)` を layout aware に
* [ ] `build_address_map_from_devices(mode, specs, layout=)` が layout を参照（窓くり抜き有無）
* [ ] `_make_sim()` / `_resolve_device_specs()` に layout を通す（既定 = circuit_compat）
* [ ] `reset_pc` を layout 由来に（既定 0x0000）
* [ ] default 互換テスト追加
* [ ] `game16` layout は**設計のみ or optional**

## 3. テスト予定（今回は未追加）

* [ ] default layout が現行互換（`circuit_compat`）
* [ ] Address Map dict が既存と一致
* [ ] UART `0x0100` 互換
* [ ] RAM 64KB（circuit）/ 256B（legacy）互換
* [ ] legacy mode 互換
* [ ] layout 候補（`legacy`/`circuit_compat`/案 `game16`）の base/size/mmio_base が期待どおり
* [ ] MMIO 複数窓配置（既定 0x0100/0x0110…）
* [ ] RAM 縮小 layout（採用するなら）で RAM/MMIO 非 overlap
* [ ] Hello World / ram_selftest / fib が壊れない
* [ ] 既存 v07/v08（address map / plan-driven / cpu-ram / target cpu / device registry / multi RAM-UART）が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: 既定で Write→Run が従来どおり（UART 出力・Address Map summary）
* [ ] 既存 project（system.json）round-trip が不変

## 5. 完了条件

* [ ] layout 設計（`MemoryLayout`）が明確になっている
* [ ] 既存互換を維持できる実装範囲が明確（既定 = circuit_compat）
* [ ] RAM サイズ可変 / MMIO 再配置の土台（layout 引数の配線）ができている
* [ ] 既定で Address Map dict・UART 0x0100・RAM 64KB・Hello World が不変
* [ ] 次の `PATCH_ADDRESS_MAP_EDITOR_V08` / `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` へ進める土台ができている
