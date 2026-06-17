# AKDev CHECKLIST 8

> v0.8 進捗管理チェックリスト（**候補整理のみ**。実装は未着手）。
> **現行の管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md`。**
> 設計詳細・候補は `ROADMAP8.md` を参照。
> v0.7 の進捗は `old/CHECKLIST7.md`（✅ v0.7 PHASE COMPLETE・履歴保管）を参照。
> v0.6 以前（`old/ROADMAP6.md`〜・`old/CHECKLIST6.md`〜）も `old/` に収納済み。

---

# 0. v0.8 開始準備

* [x] `ROADMAP8.md` を作成した（候補整理）
* [x] `CHECKLIST8.md` を作成した
* [x] 前フェーズ資料を `old/` へ整理した（2026-06-17）
  - `git mv` で `ROADMAP6.md` / `CHECKLIST6.md` / `ROADMAP7.md` / `CHECKLIST7.md` を `old/` へ収納
  - root の現行管理ファイルは `ROADMAP8.md` / `CHECKLIST8.md` のみ（v0.6 / v0.7 は完了済み履歴）
* [x] v0.8 最初の候補として `PATCH_PORT_SCHEMA_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_PORT_SCHEMA_V08_ROADMAP.md` / `PATCH_PORT_SCHEMA_V08_CHECKLIST.md`
* [x] `PATCH_PORT_SCHEMA_V08` 実装完了（2026-06-17）
  - `core/ports.py` 追加 / `parts/**/part.json` 11 種を v2 へ migration / `ui/lib.py` 正規化 / `ui/port_detail.py` 明示値優先表示
  - `python -m pytest tests/` → **878 passed**（860 + 新規 18）
  - 次候補: `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08`（接続時 direction/width 検証）
* [x] 次候補 `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_PORT_DIRECTION_WIDTH_VALIDATION_V08` 実装完了（2026-06-17・**warning only**）
  - `core/port_validation.py` 追加 / `ui/canvas.py` 接続時検証+API / `ui/port_detail.py` Validation 表示
  - `python -m pytest tests/` → **913 passed**（878 + 新規 35）
  - 次候補: `PATCH_BUS_PROTOCOL_VALIDATION_V08`（1 master 制約・到達性）
* [x] 次候補 `PATCH_BUS_PROTOCOL_VALIDATION_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_BUS_PROTOCOL_VALIDATION_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_BUS_PROTOCOL_VALIDATION_V08` 実装完了（2026-06-17・**warning only**）
  - `core/bus_validation.py` 追加 / `ui/canvas.py` bus validation API+Log / `ui/port_detail.py` bus issue 表示
  - `python -m pytest tests/` → **937 passed**（913 + 新規 24）
  - 次候補: `PATCH_DEVICE_REGISTRY_REFACTOR_V08` または `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`
* [x] 次候補 `PATCH_DEVICE_REGISTRY_REFACTOR_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_DEVICE_REGISTRY_REFACTOR_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_DEVICE_REGISTRY_REFACTOR_V08` 実装完了（2026-06-17・**挙動不変リファクタ**）
  - `core/devices.py` 追加 / `core/circuit.py` に `build_address_map_from_devices`（`build_address_map` は委譲）/ `ui/win.py:_make_sim` を device spec 駆動に分割
  - `mem.vram` を part_id ベースで分類し RAM 化しない土台
  - `python -m pytest tests/` → **957 passed**（937 + 新規 20）
  - 次候補: `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08`
* [x] 次候補 `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_MULTI_RAM_UART_ADDRESS_MAP_V08` 実装完了（2026-06-17・**単一構成完全互換**）
  - `resolve_circuit` を `device_kind` ベースへ（VRAM≠RAM 本修正・rams/uarts を node_id ソート）/ `core/devices.py` に `assign_mmio_bases`・`multi_device_warnings` / `ui/win.py` を複数 UART 配置 + 複数 RAM warning へ
  - 複数 UART = 0x0100/0x0110/0x0120…（RAM を複数窓カービング）、runtime は 1 個目互換、複数 RAM は warning
  - `python -m pytest tests/` → **973 passed**（957 + 新規 16）
  - 次候補: `PATCH_ADDRESS_MAP_EDITOR_V08` または `PATCH_CODE_REGION_MMIO_RELOCATION_V08`
* [x] 次候補 `PATCH_CODE_REGION_MMIO_RELOCATION_V08` の設計資料を作成した（2026-06-17）
  - `PATCH_CODE_REGION_MMIO_RELOCATION_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_CODE_REGION_MMIO_RELOCATION_V08` 実装完了（2026-06-17・**既定は現行互換**）
  - `core/devices.py` に `MemoryLayout`（LEGACY/CIRCUIT_COMPAT 既定/GAME16 design-only）+ `get_memory_layout` / `make_device_spec`・`assign_mmio_bases`・`build_address_map_from_devices`・`_make_sim` を layout aware に / `reset_pc` を layout 由来
  - 既定 = circuit_compat = 現行（Address Map dict・UART 0x0100・RAM 64KB・reset_pc 0x0000 不変）
  - `python -m pytest tests/` → **988 passed**（973 + 新規 15）
  - 次候補: `PATCH_ADDRESS_MAP_EDITOR_V08` または `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08`
* [x] 次候補 `PATCH_ADDRESS_MAP_EDITOR_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_ADDRESS_MAP_EDITOR_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_ADDRESS_MAP_EDITOR_V08` 実装完了（2026-06-18・**override 無しは現行互換**）
  - `ui/address_map_editor.py`（Dock + 表 + Apply/Reset/Refresh）/ `core/devices.py` に `apply_address_overrides`・`parse_address_int` / `core/circuit.py` に `validate_address_overrides` / `ui/win.py` を `_auto_device_specs`+override 分割・editor API・persist
  - GUI で per-device base/size override（auto/manual・Reset to Auto・range/overlap/align validation・error は Apply ブロック）・system.json 永続化
  - `python -m pytest tests/` → **1011 passed**（988 + 新規 23）
  - 次候補: `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` または `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
* [x] 分割先行候補 `PATCH_INPUT_DEVICE_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_INPUT_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`
* [x] `PATCH_INPUT_DEVICE_V08` 実装完了（2026-06-18・**Input 非配置は現行互換**）
  - `parts/io/input/part.json` 追加 / `core/devices.py`（input kind/role/runtime・`assign_mmio_bases` を kind 単位 backing）/ `core/dev.py` `InputPart` / `core/circuit.py` `resolve_circuit` に `inputs`/`devices` / `ui/win.py` Input runtime + `set_input_keys`
  - CPU は既存 `LD` で Input を読む（`IN` 命令不要）。UART+Input で UART 0x0100 / Input 0x0110・両 backed
  - `python -m pytest tests/` → **1034 passed**（1011 + 新規 23）
  - 次候補: `PATCH_ROM_DEVICE_V08` または `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
* [x] 次候補 `PATCH_ROM_DEVICE_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_ROM_DEVICE_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・ROM 単独（read-only memory・`sim_rom`）・既定 circuit_compat は RAM ロード維持・ROM 配置は game16 / Editor override・Program loader は RAM のまま（ROM target 化は後続）・ROM 非配置は現行互換**
* [x] `PATCH_ROM_DEVICE_V08` 実装完了（2026-06-18・**ROM 非配置は現行互換**）
  - `parts/mem/rom/part.json` 追加 / `core/devices.py`（rom kind/runtime・`MemoryLayout` に `rom_base`/`rom_size`・`_base_size` ROM 分岐・GAME16 0x0000/0x8000）/ `core/dev.py` `RomPart`（read-only・reset 保持・load_bytes/dump）/ `core/circuit.py` `resolve_circuit` に `roms` / `ui/win.py` ROM runtime（`self._sim_rom`・base 有りのみ runtime 化）
  - read-only（CPU/bus write は no-op）。circuit_compat は base 無し→未配置（Editor override で配置・RAM 縮小要）。game16 は ROM 0x0000 / RAM 0x8000 非重複。**Program loader は RAM ロードのまま**（ROM target 化は後続）
  - `python -m pytest tests/` → **1059 passed**（1034 + 新規 25）
  - 次候補: `PATCH_PROGRAM_TARGET_ROM_V08` または `PATCH_AK32_INSTRUCTION_EXPANSION_V08`
* [x] 次候補 `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` の設計資料を作成した（2026-06-18）
  - `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・ROM/Input 優先（Input は LD で読め IN 命令不要）・VRAM/Storage は後続・新 device 無しは現行互換・分割案（INPUT 先行 → ROM）あり**
* [ ] v0.8 テーマを確定する（候補: Device Expansion & Connection Validation）
  - 完了条件: ユーザーがテーマと最初のパッチを決定する
* [ ] 最初のパッチ（`PATCH_PORT_SCHEMA_V08` 想定）の実装範囲をユーザーが承認する
  - 完了条件: ユーザーから実装開始の明示的な指示がある
* [ ] 最初のパッチの `PATCH_*_V08_ROADMAP.md` / `..._CHECKLIST.md` を作業前に作成する
  - `PATCH_PORT_SCHEMA_V08` は設計資料作成済み（実装着手は承認後）

---

# 1. v0.8 作業候補（未確定・着手時に個別 CHECKLIST 化）

> 以下は候補。優先順位・取捨選択はユーザー判断で確定する。実装項目化は着手時に行う。

* [ ] A. Port direction / width validation
* [ ] B. Bus protocol validation
* [ ] C. 複数 RAM / UART handling
* [ ] D. ROM / VRAM / Storage / Input device expansion
* [ ] E. Address Map Editor
* [ ] F. コード領域拡張 / UART MMIO 窓の再配置・可変化
* [ ] G. CPU 命令拡張（CALL / RET / IN）
* [ ] H. ゲーム runtime 準備
* [ ] I. HDL / FPGA export 準備

---

# 2. 繰越課題（v0.6 → v0.7 → v0.8）

* [ ] `tests/test/system.json` のテスト実行差分の扱いをユーザーが決定する
  - 完了条件: 破棄 / コミット / .gitignore 化 のいずれかをユーザーが選ぶ（勝手に破棄しない）

---

# 3. 注意事項

* このフェーズは候補整理のみ。新機能実装・挙動変更・テスト追加・commit / push は未実施。
* 実装は、ユーザーが最初のパッチを指示してから着手する。
