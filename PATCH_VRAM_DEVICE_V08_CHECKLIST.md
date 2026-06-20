# PATCH_VRAM_DEVICE_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_VRAM_DEVICE_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現状は **実装完了・テスト全通過（1164 passed）**。
> VRAM は **書き込み可能な memory device**（CPU 命令追加なし・既存 `LD`/`ST`・reset で 0 クリア）。表示 UI は後続。commit/push は未実施。

---

## 0. 事前確認

* [x] `git status --short` がクリーン
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1136 passed**）
* [x] `dev` ブランチである
* [x] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [x] `PATCH_TIMER_DEVICE_V08` が完了・コミット済み（`cda67b6`）
* [x] `PATCH_AK32_BITWISE_INSTRUCTIONS_V08`（`3950180`）/ `PATCH_PROGRAM_TARGET_ROM_V08`（`baf5fe3`）/ `PATCH_ROM_DEVICE_V08`（`fcfa19f`）/ `PATCH_INPUT_DEVICE_V08`（`18a58b3`）/ 以前の v0.8 がコミット済み
* [x] `tests/test/system.json` に差分が無い
* [x] device registry を確認（`core/devices.py` — `_KIND_BY_PART_ID["mem.vram"]="vram"` / `_ROLE_BY_KIND["vram"]="memory"` / `_LABEL_BY_KIND["vram"]="VRAM"` / `_MEMORY_KINDS` に vram は**既存**。`_RUNTIME_BACKED` / `_RUNTIME_ID` / `_base_size` は vram 未対応）
* [x] `MemoryLayout` を確認（`vram_base`/`vram_size` フィールド無し・GAME16 は rom/ram/mmio のみ・VRAM 0xC000 はコメントのみ）
* [x] Address Map を確認（`build_address_map_from_devices` は `_MEMORY_KINDS`=ram/vram/rom を memory コンテナとして汎用処理＝VRAM 対応済み・memory 非重複前提）
* [x] RAM/ROM/Timer/VRAM 配置方針を確認（circuit_compat は RAM 全域＝VRAM は override 必須・RAM 縮小要・ROM と同じ事情）
* [x] CPU bus アクセス単位を確認（32bit LE word・`RamPart`/`RomPart` の `_offset` ベース・範囲外 `BusError`）

## 1. 設計

* [x] VRAM 仕様（part_id `mem.vram` / kind `vram` / role `memory` / runtime_id `sim_vram` / writable / reset 0 クリア）
* [x] 容量/形式（indexed color 32×32 / 1 byte/pixel / 1024 B・palette は後続・dump/pixel ビュー）
* [x] Address Map 方針（circuit_compat は base 無し=Editor override 必須 / game16 で `vram_base`=0xC000 自動案 / legacy 非使用 / VRAM/RAM/ROM overlap=error）
* [x] VramPart 方針（32bit LE word read/write・reset 0 クリア・dump/pixel/set_pixel・範囲外 BusError・word と pixel は同 bytearray）
* [x] CPU/ASM 方針（命令追加なし・既存 `LD`/`ST`・`LDI` で base・ASM 変更なし）
* [x] UI/表示方針（表示 panel は今回なし・Run Status に `VRAM:` 程度・dump/tests 優先・viewer は後続）
* [x] resolve_circuit 方針（`plan["vrams"]` 追加・既存キー互換・早期 return に vrams:[]・VRAM は必須にしない）
* [x] device registry 方針（`_RUNTIME_BACKED`/`_RUNTIME_ID` に vram・`_base_size` vram 分岐・1 個目のみ runtime-backed・kind/role/label は既存）
* [x] part.json 方針（`parts/mem/vram/part.json`・v2・ports bus/clk/reset・mem.ram/mem.rom と同形・既存有無を確認）
* [x] テスト方針（part/registry/Address Map/VramPart/CPU LD・ST/ROM target+VRAM/既存互換）
* [x] 既存互換方針（VRAM 非配置は dict 一致・CPU 命令/ASM 不変・system.json 差分なし）

## 2. 実装（完了）

* [x] part.json 追加 or 既存確認（`parts/mem/vram/part.json`・v2・ports bus/clk/reset）
* [x] device registry 追加（`core/devices.py` `_RUNTIME_BACKED` に vram / `_RUNTIME_ID["vram"]="sim_vram"` / `_base_size` vram 分岐 / `MemoryLayout` に `vram_base`/`vram_size`・GAME16=0xC000/0x0400 採用）
* [x] VramPart 追加（`core/dev.py` — 32bit LE word read/write・reset 0 クリア・dump/pixel/set_pixel・範囲外 BusError）
* [x] resolve_circuit vrams 追加（`core/circuit.py` `_is_vram` + `plan["vrams"]`・早期 return に vrams:[]・devices は既収集）
* [x] runtime 生成（`ui/win.py` `_auto_device_specs` で vrams を spec 化 / `_build_runtime_devices` で 1 個目 VRAM（base 有り）を runtime 化・`self._sim_vram` / `_sim_vram_node`・parts_by_id に sim_vram・`seen_vram` dedup）
* [x] Address Map 統合（VRAM が memory device として載る・既存 `build_address_map_from_devices` で動作・Editor override 対応）
* [x] Run Status 表示（`ui/run_status.py` `VRAM: base=.. size=..` / 非配置は `VRAM: None`）
* [x] tests 追加（`tests/test_vram_device_v08.py` — 28 件）
* [x] checklist 更新（本 CHECKLIST・旧 `test_device_registry_refactor_v08.py` の vram runtime-backed 化に伴う 2 件を更新）

## 3. テスト（完了）

* [x] part/library（`mem.vram` が出る・v2 正規化）
* [x] device registry（kind=vram・role=memory・RAM 扱いしない・addressable・runtime_backed・runtime_id sim_vram・make_device_spec）
* [x] Address Map（VRAM が載る・override で配置・VRAM/RAM overlap=error・VRAM 無しは dict 一致）
* [x] VramPart unit（read/write 32bit word・reset 0 クリア・dump・pixel/set_pixel・範囲外 BusError）
* [x] CPU LD/ST integration（`ST` で VRAM 書込・`LD` で読取・MainWin override 配置）
* [x] ROM target + VRAM（ROM からコード fetch しつつ VRAM へ書く）
* [x] existing tests（Hello World / ram_selftest / Input / ROM / Program Target / Bitwise / Timer 不変）

## 4. 検証（完了）

* [x] `python -m pytest tests/`（**1164 passed**・新規テスト込み）
* [x] VRAM write/read sample（`ST [base], r` → `LD r2, [base]`・`test_cpu_writes_and_reads_vram`）
* [x] ROM target + VRAM sample（ROM から VRAM へ書く・`test_rom_target_writes_vram`）
* [x] Address Map Editor override 確認（VRAM base/size 配置・RAM 縮小・`test_vram_runtime_built_with_override`）

## 5. 完了条件

* [x] VRAM device 仕様が明確（part/kind/role=memory/runtime/writable/reset 0 クリア）
* [x] Address Map 方針が明確（circuit_compat=override / game16 案 / overlap=error / 非配置 dict 一致）
* [x] CPU から `LD`/`ST` できる方針が明確（命令追加なし・32bit word）
* [x] 表示 UI は今回やらず後続（`PATCH_GAME_RUNTIME_MINIMAL_V08` / `PATCH_VRAM_VIEWER_V08`）に分けると明確
* [x] 既存互換が守れる（VRAM 非配置は現行一致）
* [x] 次の VRAM 実装へ進める
