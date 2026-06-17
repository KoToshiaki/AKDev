# PATCH_ROM_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_ROM_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現時点では実装未着手（設計資料のみ）。
> コード変更・テスト追加・part.json 追加・commit/push は本タスクでは行わない。

---

## 0. 事前確認

* [ ] `git status --short` がクリーンであることを確認
* [ ] `python -m pytest tests/` が全通過（着手時ベースライン取得）
* [ ] `dev` ブランチである
* [ ] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [ ] `PATCH_INPUT_DEVICE_V08` が完了・コミット済み
* [ ] `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` / `PATCH_ADDRESS_MAP_EDITOR_V08` / 以前の v08 パッチがコミット済み
* [ ] `core/devices.py` を確認（`_ROLE_BY_KIND["rom"]="memory"` / `_LABEL_BY_KIND["rom"]="ROM"` / `_MEMORY_KINDS` に rom は**既存**。`_KIND_BY_PART_ID`/`_RUNTIME_BACKED`/`_RUNTIME_ID`/`_base_size` は ROM 未対応）
* [ ] `MemoryLayout` に ROM 領域フィールドが無いことを確認
* [ ] `core/dev.py` の `RamPart`（read/write/reset/load_bytes/dump）を確認
* [ ] `core/cpu.py` の fetch=`bus.read(pc)`・`reset_pc` を確認
* [ ] `resolve_circuit` が `plan["devices"]` に rom を既に収集することを確認
* [ ] part library に `mem.rom` が無いことを確認・Address Map Editor / MemoryLayout を確認

## 1. 設計

* [ ] ROM device 仕様確定（kind=rom / role=memory / addressable / runtime_backed / runtime_id sim_rom / read-only）
* [ ] memory map 方針確定（circuit_compat は overlap=Editor override 必須 / game16 で ROM 領域 auto / legacy 非使用）
* [ ] `MemoryLayout` に `rom_base`/`rom_size`（既定 None・GAME16 のみ値）を足すか確定
* [ ] program loading 方針確定（既定 RAM ロード維持・ROM への書き込み導線は後続）
* [ ] CPU/ASM 方針確定（命令追加なし・fetch は bus.read・reset_pc と ROM base の関係）
* [ ] part.json 方針確定（`parts/mem/rom/part.json`・v2・ports bus/clk/reset）
* [ ] device registry 方針確定（maps + `_base_size` ROM 分岐 + 1 個目のみ runtime-backed）
* [ ] resolve_circuit 方針確定（`plan["roms"]` 追加・既存キー互換・RAM 必須は外さない）
* [ ] runtime 方針確定（`RomPart` read/write(no-op)/reset(保持)/load_bytes/dump）
* [ ] UI/Loader 方針確定（最小は RomPart + Address Map・Write Program は RAM 維持・ROM ロードは後続）
* [ ] Address Map / Editor 方針確定（ROM/RAM overlap=error・Editor override 可・ROM 非配置は現行一致）

## 2. 実装予定（今回は未実装）

* [ ] `parts/mem/rom/part.json` 追加（v2 schema）
* [ ] `core/devices.py` `_KIND_BY_PART_ID["mem.rom"]="rom"` / `_RUNTIME_BACKED` に rom / `_RUNTIME_ID["rom"]="sim_rom"`
* [ ] `core/devices.py` `_base_size` の ROM 分岐 + `MemoryLayout` に `rom_base`/`rom_size`（GAME16 値）
* [ ] `core/dev.py` に `RomPart` 追加（read-only・reset 保持・load_bytes/dump）
* [ ] `core/circuit.py:resolve_circuit` に `plan["roms"]` 追加（devices は既に収集・互換維持）
* [ ] `ui/win.py:_auto_device_specs` が ROM も spec 化
* [ ] `ui/win.py:_build_runtime_devices` が 1 個目 ROM を runtime 化（parts_by_id に sim_rom）
* [ ] `ui/win.py` に `self._sim_rom` / `self._sim_rom_node` 追加
* [ ] Address Map 表示（ROM が載る）/ Address Map Editor override 確認
* [ ] Program loader は現行維持（RAM ロード）/ ROM への IDE ロードは後続
* [ ] tests 追加

## 3. テスト予定（今回は未追加）

* [ ] `mem.rom` が library に出る
* [ ] `device_kind("mem.rom") == "rom"` / `device_role("rom") == "memory"`
* [ ] rom が addressable / runtime_backed / runtime_id sim_rom
* [ ] `make_device_spec()` が ROM spec を作る
* [ ] `RomPart.load_bytes()` / `read()` が動く
* [ ] `RomPart.write()` しても内容不変（read-only）
* [ ] `RomPart.reset()` で内容が消えない
* [ ] ROM が Address Map に載る（layout/override で base/size）
* [ ] Address Map Editor で ROM base/size override
* [ ] ROM+RAM overlap が `ADDRESS_OVERLAP`（error）
* [ ] game16 で ROM 0x0000 / RAM 0x8000 非重複（layout を使う場合）
* [ ] ROM 非配置の既存構成は Address Map dict 完全一致
* [ ] Hello World / ram_selftest / legacy が壊れない

## 4. 検証予定

* [ ] `python -m pytest tests/` が全件通過
* [ ] GUI 目視: ROM を置く・Address Map に出る・Editor で base/size 調整・overlap 警告
* [ ] ROM 配置時の Address Map 表示（Run Status summary）
* [ ] ROM read-only 確認（write 後内容不変）
* [ ] 既存 project（system.json）round-trip 不変（ROM 無し）

## 5. 完了条件

* [ ] ROM device 方針が明確（kind/role/runtime/read-only/reset 保持）
* [ ] read-only memory として扱える設計（write no-op・reset 内容保持）
* [ ] 既定 RAM ロード互換を維持（ROM 非配置で現行完全一致・Hello World/selftest/legacy）
* [ ] ROM/RAM overlap の扱い（circuit_compat=override 必須 / game16=非重複）が明確
* [ ] 次の `PATCH_PROGRAM_TARGET_ROM_V08` / `PATCH_AK32_INSTRUCTION_EXPANSION_V08` へ進める