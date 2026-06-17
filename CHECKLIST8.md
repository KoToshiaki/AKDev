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
  - `PATCH_CODE_REGION_MMIO_RELOCATION_V08_ROADMAP.md` / `..._CHECKLIST.md`。**実装は未着手・`MemoryLayout`（legacy/circuit_compat/game16 案）土台・既定は現行互換**
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
