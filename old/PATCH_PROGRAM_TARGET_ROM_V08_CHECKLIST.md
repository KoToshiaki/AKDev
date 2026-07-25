# PATCH_PROGRAM_TARGET_ROM_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_PROGRAM_TARGET_ROM_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。**実装完了（2026-06-19・`python -m pytest tests/` 1080 passed）**。
> 既定 target は RAM（既存互換）。ROM target は ROM runtime（base 確定）がある時のみ有効。commit/push は未実施。

---

## 0. 事前確認

* [x] `git status --short` がクリーン
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1059 passed**）
* [x] `dev` ブランチである
* [x] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [x] `PATCH_ROM_DEVICE_V08` が完了・コミット済み（`fcfa19f`）
* [x] `PATCH_INPUT_DEVICE_V08` が完了・コミット済み（`18a58b3`）
* [x] 以前の v0.8 パッチがコミット済み（port schema 〜 address map editor 〜 rom）
* [x] `tests/test/system.json` に差分が無い
* [x] `RomPart`（`core/dev.py`）を確認（read / write=no-op / reset=保持 / `load_bytes`（size 超過=ValueError） / `dump` / `base` / `size`）
* [x] Program loader を確認（`write_program` → `_bind_circuit_runtime` → `_assemble_and_load` → `runtime.load_program` が RAM hardcode）
* [x] system.json persist を確認（`_persist_system` が `parts` / `address_map_overrides` を保存・`load_project` が復元）
* [x] reset_pc を確認（`AK32Part(reset_pc=layout.reset_pc)`・構築時固定・setter 無し・`_build_runtime_devices` で rebuild）
* [x] Address Map validation を確認（ROM/RAM overlap=`ADDRESS_OVERLAP` error・Editor override）
* [x] `self._sim_rom` / `self._sim_rom_node`（base 確定時のみ構築）を確認

## 1. 設計

* [x] program target 仕様（`ram` 既定 / `rom` は ROM runtime 確定時のみ / `auto` は後続）
* [x] project 永続化方針（system.json `program_target`・無/不正→`ram`・round-trip 互換）
* [x] UI 方針（最小は状態+API・可能なら Run/Debug 付近に RAM/ROM ComboBox・ROM 不成立は無効化/warning）
* [x] loader 方針（RAM=現行 `runtime.load_program` 維持 / ROM=`RomPart.load_bytes`・分岐は MainWin に閉じる）
* [x] reset_pc 方針（ROM target かつ base 確定→`reset_pc=rom.base`・rebuild 時に決定・不成立は error）
* [x] Address Map / Layout 方針（circuit_compat=override 必須 / game16=ROM 0x0000 自然 / overlap は ROM target 不可）
* [x] CPU/ASM 方針（命令追加なし・ASM 拡張なし・ORG/linker は後続・base=0x0000 を主対象）
* [x] error / diagnostic 方針（ROM 無し/未配置/overlap/size 超過/不正値の扱いと出力先）
* [x] 既存互換方針（既定 RAM・既存 project=RAM・Hello World/selftest/legacy 不変・ROM 非配置 dict 一致）

## 2. 実装（`ui/win.py` / `ui/run_status.py`）

* [x] `self._program_target`（既定 `"ram"`・`__init__` で `_setup_sim` 前に設定）+ `_normalize_program_target`（無/不正→`ram`・staticmethod）追加
* [x] project load/save/new 対応（`_open_project` 復元 / `_persist_system` で `system["program_target"]` 保存 / `_new_project` で `"ram"` / `_save_project_as` は現在値を保存）
* [x] target setter/getter（`set_program_target`（不正値 warning・status log・`_update_run_status`・persist）/ `program_target` / `_program_target_status` / `_rom_runtime_ready`）
* [x] Write Program 分岐（`_assemble_and_load` で `program_target` により RAM/ROM・ROM 失敗時は RAM へ書かず False）
* [x] RAM loader 維持（`_load_program_to_ram` = 現行 `runtime.load_program`・`VirtualCircuitRuntime.load_program` は不変）
* [x] ROM loader 追加（`_load_program_to_rom` = validate → `self._sim_rom.load_bytes` → RAM clear + `runtime.reset()` + loaded フラグ）
* [x] ROM target validation（ROM 無し / base 未確定 / Address Map overlap / size 超過 → error・False）
* [x] reset_pc 処理（`_build_runtime_devices` で ROM target かつ ROM base 確定時に CPU `reset_pc=rom.base`・pre-pass で解決）
* [x] UI 最小対応（API + Run Status に `Program Target:` 行を追加。ribbon ComboBox は範囲外。`_program_target_status` で `RAM`/`ROM @0x..`/`ROM (unplaced)`）
* [x] tests 追加（`tests/test_program_target_rom_v08.py` — 21 件）

## 3. テスト（`tests/test_program_target_rom_v08.py` — 21 件）

* [x] project persist（`program_target` が `system.json` へ保存・`_persist_system`）
* [x] RAM target 互換（既定 RAM・Hello World・ram_selftest・legacy・reset_pc=layout・RAM へロード・ROM 不変）
* [x] ROM target load（`RomPart.load_bytes` に binary・RAM clear・runtime loaded・ROM へ書く）
* [x] reset_pc（ROM target で CPU `reset_pc=rom.base`・`cpu.pc()` が ROM base 始まり）
* [x] ROM fetch（ROM 0x0000 から `LDI r1,123; HALT` を fetch・実行後 `r1==123`・halted）
* [x] error handling（ROM 無し / 未配置 / overlap（apply 拒否 + loader guard）/ size 超過 → False・RAM 非ロード）
* [x] 不正 `program_target` は RAM fallback（`_normalize_program_target` / system.json / `set_program_target`）
* [x] status（`_program_target_status` 3 状態・Run Status に `Program Target: RAM` 表示）
* [x] existing tests（Hello World / ram_selftest / legacy / input / rom / address map editor 不変）

## 4. 検証

* [x] `python -m pytest tests/` 全件通過 — **1080 passed**（1059 + 21）
* [ ] GUI 目視（Run Status の `Program Target` 行・ROM fetch 実行。ヘッドレスのため未実施）
* [x] RAM target Hello World（現行どおり RAM 実行・テストで実証）
* [x] ROM target simple program（circuit_compat + override で ROM 0x0000・fetch・実行・テストで実証）
* [x] `tests/test/system.json` に差分なし（tmp_path project のみ使用）

## 5. 完了条件

* [x] RAM/ROM target 方針が明確（仕様 / 永続化 / loader / reset_pc / error）
* [x] RAM 既定互換が守れる（既存 project=RAM・Hello World/selftest/legacy 不変・dict 一致）
* [x] ROM に loader（`RomPart.load_bytes`）で書ける（CPU/bus write は no-op のまま・実装/テスト実証）
* [x] ROM target 時に ROM base から fetch できる（reset_pc=rom.base・実行テスト実証）
* [x] 次の実装（`PATCH_AK32_INSTRUCTION_EXPANSION_V08` / `PATCH_TIMER_DEVICE_V08` 等）へ進める
