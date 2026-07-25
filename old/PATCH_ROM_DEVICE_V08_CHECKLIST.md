# PATCH_ROM_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_ROM_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。**実装完了（2026-06-18・`python -m pytest tests/` 1059 passed）**。
> Program loader は RAM ロードのまま。ROM target 化は後続 `PATCH_PROGRAM_TARGET_ROM_V08`。commit/push は未実施。

---

## 0. 事前確認

* [x] `git status --short` がクリーンであることを確認
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1034 passed**）
* [x] `dev` ブランチである
* [x] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [x] `PATCH_ROM_DEVICE_V08`（設計）が完了・コミット済み（`6a42451`）
* [x] `PATCH_INPUT_DEVICE_V08` が完了・コミット済み（`18a58b3`）
* [x] `PATCH_DEVICE_EXPANSION_ROM_INPUT_V08` / `PATCH_ADDRESS_MAP_EDITOR_V08` / 以前の v08 パッチがコミット済み
* [x] `core/devices.py` を確認（`_ROLE_BY_KIND["rom"]="memory"` / `_LABEL_BY_KIND["rom"]="ROM"` / `_MEMORY_KINDS` に rom は**既存**。`_KIND_BY_PART_ID`/`_RUNTIME_BACKED`/`_RUNTIME_ID`/`_base_size` は ROM 未対応だった）
* [x] `MemoryLayout` に ROM 領域フィールドが無いことを確認
* [x] `core/dev.py` の `RamPart`（read/write/reset/load_bytes/dump）を確認
* [x] `core/cpu.py` の fetch=`bus.read(pc)`・`reset_pc` を確認
* [x] `resolve_circuit` が `plan["devices"]` に rom を既に収集することを確認
* [x] part library に `mem.rom` が無いことを確認・Address Map Editor / MemoryLayout を確認

## 1. 設計

* [x] ROM device 仕様確定（kind=rom / role=memory / addressable / runtime_backed / runtime_id sim_rom / read-only）
* [x] memory map 方針確定（circuit_compat は base 無し=Editor override 必須 / game16 で ROM 領域 auto / legacy 非使用）
* [x] `MemoryLayout` に `rom_base`/`rom_size`（既定 None・GAME16 0x0000/0x8000）を追加
* [x] program loading 方針確定（既定 RAM ロード維持・ROM への書き込み導線は後続）
* [x] CPU/ASM 方針確定（命令追加なし・fetch は bus.read・reset_pc は layout 既定 0x0000）
* [x] part.json 方針確定（`parts/mem/rom/part.json`・v2・ports bus/clk/reset）
* [x] device registry 方針確定（maps + `_base_size` ROM 分岐 + 1 個目のみ runtime-backed）
* [x] resolve_circuit 方針確定（`plan["roms"]` 追加・既存キー互換・RAM 必須は外さない）
* [x] runtime 方針確定（`RomPart` read/write(no-op)/reset(保持)/load_bytes/dump）
* [x] UI/Loader 方針確定（最小は RomPart + Address Map・Write Program は RAM 維持・ROM ロードは後続）
* [x] Address Map / Editor 方針確定（ROM/RAM overlap=error・Editor override 可・ROM 非配置は現行一致）

## 2. 実装

* [x] `parts/mem/rom/part.json` 追加（v2 schema）
* [x] `core/devices.py` `_KIND_BY_PART_ID["mem.rom"]="rom"` / `_RUNTIME_BACKED` に rom / `_RUNTIME_ID["rom"]="sim_rom"`
* [x] `core/devices.py` `_base_size` の ROM 分岐 + `MemoryLayout` に `rom_base`/`rom_size`（GAME16 値）
* [x] `core/dev.py` に `RomPart` 追加（read-only・reset 保持・load_bytes/dump）
* [x] `core/circuit.py:resolve_circuit` に `_is_rom` + `plan["roms"]` 追加（devices は既に収集・互換維持）
* [x] `ui/win.py:_auto_device_specs` が ROM も spec 化
* [x] `ui/win.py:_build_runtime_devices` が 1 個目 ROM（base 有り）を runtime 化（parts_by_id に sim_rom・base None ROM は addr_specs から除外）
* [x] `ui/win.py` に `self._sim_rom` / `self._sim_rom_node` 追加・`RomPart` import
* [x] Address Map 表示（ROM が載る）/ Address Map Editor override 対応（既存ロジックで動作）
* [x] Program loader は現行維持（RAM ロード）/ ROM への IDE ロードは後続
* [x] tests 追加

## 3. テスト（`tests/test_rom_device_v08.py` — 25 件）

* [x] `mem.rom` が library に出る（v2 schema 正規化）
* [x] `device_kind("mem.rom") == "rom"` / `device_role("rom") == "memory"` / addressable・runtime_backed
* [x] `make_device_spec()` が ROM spec を作る（game16=0x0000/0x8000・circuit_compat は base None）
* [x] `MemoryLayout`: circuit_compat/legacy の rom_base/rom_size None・game16 0x0000/0x8000・既存 RAM/MMIO 値不変
* [x] `RomPart.load_bytes()` / `read()`（32bit LE word）・base offset
* [x] `RomPart.write()` しても内容不変（read-only・例外なし）
* [x] `RomPart.reset()` で内容が消えない
* [x] `RomPart.dump()` / 範囲外 read=BusError・範囲外 write=no-op
* [x] `resolve_circuit`: ROM 収集 / ROM 無し不変 / 未接続 ROM 非収集 / devices に rom
* [x] game16 で ROM 0x0000 / RAM 0x8000 非重複・ROM+RAM overlap 検出
* [x] MainWin: 既定 circuit_compat で ROM 非配置（base 無し→未配置・Hello World 通る）
* [x] MainWin: override で `self._sim_rom` 構築・Address Map に ROM・read-only（bus write 無視）
* [x] MainWin: Editor に ROM 表示・ROM+RAM overlap が Apply ブロック（error）
* [x] ROM 無し構成は既存 Address Map dict 一致・Hello World / ram_selftest / legacy 不変

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **1059 passed**（1034 + 25）
* [ ] GUI 目視: ROM 配置・Address Map 表示・Editor で base/size 調整・overlap 警告（ヘッドレスのため未実施）
* [x] ROM read-only 確認（bus write 後内容不変・unit + MainWin）
* [x] 既存 project（system.json）round-trip 不変（ROM 無し・既存テスト通過・system.json 差分なし）

## 5. 完了条件

* [x] ROM device 方針が明確（kind/role/runtime/read-only/reset 保持）
* [x] read-only memory として扱える（write no-op・reset 内容保持）が実装・テストで実証
* [x] 既定 RAM ロード互換を維持（ROM 非配置で現行完全一致・Hello World/selftest/legacy）
* [x] ROM/RAM overlap の扱い（circuit_compat=override 必須 / game16=非重複）が明確・テスト済み
* [x] 次の `PATCH_PROGRAM_TARGET_ROM_V08` / `PATCH_AK32_INSTRUCTION_EXPANSION_V08` へ進める土台ができている