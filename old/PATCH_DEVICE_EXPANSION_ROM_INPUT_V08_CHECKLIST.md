# PATCH_DEVICE_EXPANSION_ROM_INPUT_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 追加・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `PATCH_ADDRESS_MAP_EDITOR_V08` が完了・コミット済みであることを確認
* [ ] `PATCH_CODE_REGION_MMIO_RELOCATION_V08`（MemoryLayout）/ 以前の v08 パッチが完了・コミット済み
* [ ] `core/devices.py` の `device_kind`/`_KIND_BY_PART_ID`/`_ROLE_BY_KIND`/`_RUNTIME_BACKED`/`_RUNTIME_ID`/`make_device_spec`/`assign_mmio_bases` を確認
* [ ] `core/dev.py` の `RamPart`/`UartPart`（read/write/reset/load_bytes/dump）を確認
* [ ] `core/cpu.py` の `LD`（=bus.read）= MMIO read 可・`IN` 命令が無いことを確認
* [ ] `core/circuit.py:resolve_circuit`（cpu/ram/uart のみ収集）/ `ui/win.py:_auto_device_specs`/`_build_runtime_devices` を確認
* [ ] part library（`mem.rom`/`io.input` が無い・gpio/timer/vram は有る）を確認
* [ ] Address Map Editor（override/validation）を確認

## 1. 設計

* [ ] 追加 device 候補確定（今回: ROM / Input。後続: Timer/GPIO/VRAM/Video/Storage）
* [ ] ROM 方針確定（read-only RomPart・circuit_compat は既定 RAM ロード維持・game16/Editor で ROM 配置・reset_pc=code_base）
* [ ] Input 方針確定（MMIO・KEY_STATE/EDGE_STATE・**LD で読む**・set_keys 供給・IN 命令不要）
* [ ] Timer/GPIO 方針確定（後続・MMIO・別窓）
* [ ] VRAM/Video 方針確定（後続・memory・game16 前提・描画は別パッチ）
* [ ] Address Map 方針確定（circuit_compat は新 device 無しで現行一致・Editor override 可・assign_mmio_bases に input）
* [ ] runtime 方針確定（RomPart/InputPart を Bus device 追加・1 個目のみ backed・runtime_id sim_rom/sim_input）
* [ ] CPU/ASM との関係確定（命令・assembler 拡張なし・MMIO は LD・ROM fetch は reset_pc 設定）
* [ ] 分割するか確定（推奨: `PATCH_INPUT_DEVICE_V08` 先行 → `PATCH_ROM_DEVICE_V08`）
* [ ] resolve_circuit を「wired addressable device 全 kind 収集」へ拡張する方針確定（cpu/rams/uarts 互換維持）

## 2. 実装予定（今回は未実装）

* [ ] part.json 追加（`mem.rom` / `io.input`・v2 schema）
* [ ] `core/devices.py` `_KIND_BY_PART_ID` に rom/input 追加
* [ ] `device_role` / `_ROLE_BY_KIND`（rom=memory / input=mmio）更新
* [ ] `is_addressable_kind` / `is_runtime_backed_kind`（`_RUNTIME_BACKED` に rom/input）更新
* [ ] `_RUNTIME_ID`（rom→sim_rom / input→sim_input）/ `_LABEL_BY_KIND` 更新
* [ ] `make_device_spec` が rom/input を正しく spec 化（base/size は layout/MMIO 割当）
* [ ] `core/dev.py` に `RomPart`（read-only）/ `InputPart`（MMIO + set_keys）追加
* [ ] `core/circuit.py:resolve_circuit` を device 収集拡張（`plan["devices"]` 等・互換維持）
* [ ] `ui/win.py:_auto_device_specs` / `_build_runtime_devices` を ROM/Input 対応
* [ ] Address Map 表示 + Address Map Editor override 対応（既存ロジック流用）
* [ ] Input 供給 UI（Debug の virtual buttons / keyboard → InputPart.set_keys）
* [ ] tests 追加

## 3. テスト予定（今回は未追加）

* [ ] part library に `mem.rom` / `io.input` が出る
* [ ] `device_kind`: mem.rom→rom / io.input→input・role/addressable/runtime_backed
* [ ] `make_device_spec` の rom/input spec
* [ ] Address Map に ROM/Input が載る・Editor override・overlap validation
* [ ] runtime read/write（RomPart read-only / InputPart read）
* [ ] Input が `set_keys` → `LD`/bus.read で読める
* [ ] ROM が read-only（write 後内容不変）・load_bytes/dump
* [ ] resolve_circuit が ROM/Input を収集（cpu/rams/uarts 互換）
* [ ] 既存 CPU/RAM/UART 構成は壊れない（新 device 無しで Address Map dict 一致）
* [ ] Hello World / ram_selftest / legacy が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: ROM/Input を置く・Address Map に出る・Editor で base/size 調整・Input ボタンで CPU が反応
* [ ] 既存 project（system.json）round-trip 不変（新 device 無し）
* [ ] 新 device を置いたときの Address Map 表示

## 5. 完了条件

* [ ] 追加 device 方針が明確（今回 ROM/Input・後続 Timer/GPIO/VRAM/Storage）
* [ ] ROM / Input の優先実装範囲が明確（分割案含む）
* [ ] 既存互換を維持できる（新 device 無しで現行完全一致）方針が明確
* [ ] resolve_circuit の device 収集拡張方針が固まっている
* [ ] 次の実装（`PATCH_INPUT_DEVICE_V08` / `PATCH_ROM_DEVICE_V08` / `PATCH_AK32_INSTRUCTION_EXPANSION_V08`）へ進める
