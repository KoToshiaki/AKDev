# PATCH_AK32_INSTRUCTION_EXPANSION_V08 — CHECKLIST（設計資料・親計画）

> 設計詳細は `PATCH_AK32_INSTRUCTION_EXPANSION_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現状は **設計のみ完了・実装は未着手**。
> 本パッチは親設計。**最初の実装は子パッチ `PATCH_AK32_BITWISE_INSTRUCTIONS_V08`（AND/OR/XOR/NOT）に限定**。
> CALL/RET/stack は `PATCH_AK32_STACK_CALL_RET_V08` に分離。commit/push は未実施。

---

## 0. 事前確認

* [x] `git status --short` がクリーン
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1080 passed**）
* [x] `dev` ブランチである
* [x] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [x] `PATCH_PROGRAM_TARGET_ROM_V08` が完了・コミット済み（`baf5fe3`）
* [x] `PATCH_ROM_DEVICE_V08`（`fcfa19f`）/ `PATCH_INPUT_DEVICE_V08`（`18a58b3`）/ 以前の v0.8 パッチがコミット済み
* [x] `tests/test/system.json` に差分が無い
* [x] 現行 CPU 命令一覧を確認（`core/cpu.py` — NOP/HALT/LDI/OUT/ADD/SUB/LD/ST/JMP/BEQ/ADDI = 11 命令・opcode 0x00–0x0A）
* [x] opcode を確認（8bit・32bit 固定長・空き 0x0B–0xFE・`0xFF` は unknown=halt 検証に使用＝予約）
* [x] ASM parser を確認（`asm/asm.py` — 2-pass・`_OPCODES` 独自表・`_parse_reg`/`_parse_deref`/`_parse_imm`/`_resolve_rel8`・ラベル）
* [x] existing CPU tests を確認（`tests/test_cpu_v04.py` — ADD/SUB/ADDI/LD/ST/JMP/BEQ・r0・Z・32bit wrap・unknown=halt）
* [x] opcode 三重管理を確認（`core/cpu.py` / `asm/asm.py` / `core/runtime.py:disasm`）

## 1. 設計

* [x] 既存命令仕様確認（format・opcode・PC 更新・HALT・BEQ 分岐条件・JMP 幅・LD/ST 間接・OUT・Z flag・r0）
* [x] 追加命令候補整理（bitwise / shift / imm bitwise / branch 拡張 / stack / convenience）
* [x] 最初の実装範囲決定（Phase 1 = `AND`/`OR`/`XOR`/`NOT` のみ・CALL/RET は除外）
* [x] opcode 方針（既存不変・末尾追記 0x0B–0x0E・0xFF 予約・単一化は任意先行 Phase 0）
* [x] instruction format 方針（既存 4 形式に寄せる・新 format を増やさない・bitwise は R-type）
* [x] ASM 構文方針（既存準拠・operand 数チェック・disasm 追加・新構文なし）
* [x] CPU 実装方針（`_execute` 分岐追加・`_set_reg` 経由・Z 更新・PC 不変・unknown=halt 不変）
* [x] stack/CALL/RET 方針（SP=r15 規約案・stack は RAM・`stack_top` 利用・今回は実装しない）
* [x] Input bit 判定サンプル（`LD`+`AND`+`BEQ`・test/example 化方針）
* [x] ROM target との関係（fetch ベースで RAM/ROM 両対応・既定 RAM・ROM target test 追加方針）
* [x] 既存互換方針（opcode 不変・既存 binary 同挙動・Hello World/selftest/fib/legacy 不変・0xFF halt）

## 2. 実装予定（今回は未実装 / 子パッチ `PATCH_AK32_BITWISE_INSTRUCTIONS_V08`）

* [ ] opcode 追加（`core/cpu.py` `OP_AND=0x0B` / `OP_OR=0x0C` / `OP_XOR=0x0D` / `OP_NOT=0x0E`）
* [ ] CPU decode 追加（`_execute` に 4 分岐・`_set_reg` 経由・Z 更新・docstring 更新）
* [ ] ASM parse 追加（`asm/asm.py` `_OPCODES` に 4 命令・encode 分岐・operand 数チェック・docstring 更新）
* [ ] disasm 追加（`core/runtime.py:disasm` に 4 命令の表示分岐）
* [ ] tests 追加（ASM encode / CPU execute / Z / r0 / 32bit mask / Input 判定 / ROM target）
* [ ] examples 追加検討（Input bit 判定サンプル ASM）
* [ ] `CHECKLIST8` 最小追記（Phase 1 実装完了・pytest 結果）
* [ ]（任意先行）`PATCH_AK32_OPCODE_TABLE_V08` で `core/opcodes.py` 単一化

## 3. テスト予定

* [ ] ASM tests（`AND`/`OR`/`XOR` 3 オペランド・`NOT` 2 オペランド encode・operand 数エラー）
* [ ] CPU execution tests（4 命令の結果・Z flag・r0 宛先 0・32bit mask・PC +4）
* [ ] Input bit 判定（`LD`+`AND`+`BEQ` で分岐）
* [ ] ROM target fetch/execute（override で ROM 配置 → `set_program_target("rom")` → write → run）
* [ ] disasm tests（新命令の文字列化）
* [ ] existing tests（Hello World / ram_selftest / fib / legacy / Input / ROM / Program Target / unknown=halt 不変）

## 4. 検証予定

* [ ] `python -m pytest tests/`（全通過・新規テスト込み）
* [ ] 簡単な bitwise program（`AND`/`OR`/`XOR`/`NOT` の手動確認）
* [ ] Input 判定 program（キーマスク → 分岐）
* [ ] ROM target program（ROM から bitwise 命令を fetch/execute）

## 5. 完了条件

* [x] 命令追加方針が明確（候補・段階分割・opcode・format・ASM・CPU・stack 設計）
* [x] 最初の実装範囲が小さく安全（Phase 1 bitwise のみ・stack 非依存・既存互換）
* [x] opcode 互換が守れる（既存 0x00–0x0A 不変・末尾追記・0xFF 予約）
* [x] 次の Bitwise 実装（`PATCH_AK32_BITWISE_INSTRUCTIONS_V08`）へ進める
