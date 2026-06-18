# PATCH_PROGRAM_TARGET_ROM_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_PROGRAM_TARGET_ROM_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現状は **設計のみ完了・実装は未着手**。
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

## 2. 実装予定（今回は未実装）

* [ ] `self._program_target`（既定 `"ram"`）+ `_normalize_target`（無/不正→`ram`）追加
* [ ] project load/save/new 対応（`_open_project` 復元 / `_persist_system` 保存 / `_new_project` / `_save_project_as` 既定 RAM）
* [ ] target setter/getter（`set_program_target` / `program_target` / `_program_target_effective` / `_program_target_status`）
* [ ] Write Program 分岐（`_assemble_and_load` で RAM/ROM）
* [ ] RAM loader 維持（`_load_program_to_ram` = 現行 `runtime.load_program`・既存挙動不変）
* [ ] ROM loader 追加（`_load_program_to_rom` = `self._sim_rom.load_bytes` + reset 系）
* [ ] ROM target validation（ROM 無し / 未配置 / overlap / size 超過 → error）
* [ ] reset_pc 処理（`_build_runtime_devices` で ROM base 確定時に CPU `reset_pc=rom.base`）
* [ ] UI 最小対応（Run/Debug 付近 ComboBox or API + status・ROM 不成立は無効化/warning）
* [ ] tests 追加

## 3. テスト予定

* [ ] project persist（`program_target` が save→load される）
* [ ] RAM target 互換（既存 Write Program 挙動・既存 project=RAM・不正値→RAM fallback）
* [ ] ROM target load（`RomPart.load_bytes` に binary・ROM 無し/未配置/size 超過は error）
* [ ] reset_pc（ROM target で CPU `reset_pc=rom.base`・`cpu.pc()` が ROM base 始まり）
* [ ] error handling（ROM 無し/未配置/overlap/size 超過/不正値）
* [ ] existing tests（Hello World / ram_selftest / legacy / input / rom 不変・Address Map dict 一致）

## 4. 検証予定

* [ ] `python -m pytest tests/`（全通過・新規テスト込み）
* [ ] GUI 目視（Program Target ComboBox 表示・ROM 不成立で無効化・status 表示。ヘッドレスは未実施理由を記録）
* [ ] RAM target Hello World（現行どおり RAM 実行）
* [ ] ROM target simple program（game16 想定・ROM 0x0000 から fetch・実行）

## 5. 完了条件

* [ ] RAM/ROM target 方針が明確（仕様 / 永続化 / loader / reset_pc / error）
* [ ] RAM 既定互換が守れる（既存 project=RAM・Hello World/selftest/legacy 不変・dict 一致）
* [ ] ROM に loader（`RomPart.load_bytes`）で書ける設計（CPU/bus write は no-op のまま）
* [ ] ROM target 時に ROM base から fetch できる設計（reset_pc=rom.base）
* [ ] 次の実装（`PATCH_AK32_INSTRUCTION_EXPANSION_V08` 等）へ進める
