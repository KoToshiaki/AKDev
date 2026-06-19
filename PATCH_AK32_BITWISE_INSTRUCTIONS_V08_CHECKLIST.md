# PATCH_AK32_BITWISE_INSTRUCTIONS_V08 — CHECKLIST（設計資料）

> 設計詳細は `PATCH_AK32_BITWISE_INSTRUCTIONS_V08_ROADMAP.md` を参照。
> 本書は**実装時に使うチェックリスト**。現状は **設計のみ完了・実装は未着手**。
> 親設計 `PATCH_AK32_INSTRUCTION_EXPANSION_V08` の Phase 1。対象は `AND`/`OR`/`XOR`/`NOT` の 4 命令のみ。
> opcode 単一化・shift・immediate bitwise・branch 拡張・CALL/RET/stack・IN は対象外。commit/push は未実施。

---

## 0. 事前確認

* [x] `git status --short` がクリーン
* [x] `python -m pytest tests/` が全通過（着手時ベースライン **1080 passed**）
* [x] `dev` ブランチである
* [x] `ROADMAP8.md` の見出し重複が無い（`# AKDev ROADMAP 8` / `## v0.8 作業候補` 各 1 回）
* [x] 親設計 `PATCH_AK32_INSTRUCTION_EXPANSION_V08` が完了・コミット済み（`6a74d36`）
* [x] `PATCH_PROGRAM_TARGET_ROM_V08`（`baf5fe3`）/ `PATCH_ROM_DEVICE_V08`（`fcfa19f`）/ `PATCH_INPUT_DEVICE_V08`（`18a58b3`）/ 以前の v0.8 がコミット済み
* [x] `tests/test/system.json` に差分が無い
* [x] 現行 CPU 命令一覧を確認（`core/cpu.py` — 11 命令・opcode 0x00–0x0A・ADD/SUB は 3 オペランド R-type・Z flag・r0 ハードワイヤ・32bit 固定長）
* [x] opcode 空きを確認（0x0B–0xFE 空き・**0xFF は unknown opcode テスト用に予約**）
* [x] ASM parser を確認（`asm/asm.py` — `_OPCODES`・`_parse_reg`・operand 数チェック・2-pass・ラベル）
* [x] disasm を確認（`core/runtime.py:disasm` — `AK32Part.OP_*` 参照・mnemonic 文字列は独自・unknown は `DW 0x..`）
* [x] existing CPU tests を確認（`tests/test_cpu_v04.py` — ADD/SUB/ADDI/LD/ST/JMP/BEQ・r0・Z・32bit wrap・`test_unknown_opcode_halts`=0xFF）
* [x] Input base / キー bit を確認（`tests/test_input_device_v08.py` — Input=0x0110・A=bit4=0x10・`set_keys`）

## 1. 設計

* [x] 対象命令確定（`AND`/`OR`/`XOR` 3 オペランド・`NOT` 2 オペランド・2 オペランド AND は不採用）
* [x] opcode 確定（`AND=0x0B` / `OR=0x0C` / `XOR=0x0D` / `NOT=0x0E`・既存不変・0xFF 予約）
* [x] format 確定（`op<<24|rd<<16|rs<<8|rt`／`NOT` は bits7..0=0・32bit 固定 LE）
* [x] ASM 構文確定（既存準拠・operand 数チェック・`_OPCODES` 追記・新構文なし・ラベル影響なし）
* [x] CPU 実装方針確定（`_execute` に 4 分岐・`_set_reg` 経由・Z 更新・32bit mask・PC +4・unknown=halt 不変）
* [x] disasm 方針確定（`AND/OR/XOR rD,rS,rT`・`NOT rD,rS`・`DW` フォールバック不変）
* [x] Input bit 判定方針（`LD`+`AND`+`BEQ`・押下/非押下の両ケース・Input 0x0110）
* [x] ROM target 統合方針（override で ROM 0x0000・`set_program_target("rom")`・fetch/execute・既存 ROM test 不変）
* [x] 既存互換方針（opcode 不変・既存 binary 同挙動・Hello World/selftest/fib/legacy/Input/ROM/Program Target 不変・0xFF halt）
* [x] opcode 単一化は今回やらず別パッチ `PATCH_AK32_OPCODE_TABLE_V08` として記録・3 か所整合はテストで担保

## 2. 実装予定（今回は未実装）

* [ ] CPU opcode 定数追加（`core/cpu.py` `OP_AND=0x0B` / `OP_OR=0x0C` / `OP_XOR=0x0D` / `OP_NOT=0x0E`）
* [ ] CPU execute 追加（`_execute` に 4 分岐・`_set_reg`・Z 更新・docstring 更新）
* [ ] ASM opcode 追加（`asm/asm.py` `_OPCODES` に 4 命令）
* [ ] ASM encode 追加（pass 2 に 4 分岐・operand 数チェック・docstring 更新）
* [ ] disasm 追加（`core/runtime.py:disasm` に 4 命令の表示分岐）
* [ ] tests 追加（`tests/test_ak32_bitwise_instructions_v08.py`）
* [ ] docs/checklist 更新（本 CHECKLIST・`CHECKLIST8.md` 最小追記）

## 3. テスト予定

* [ ] ASM encode（`AND`/`OR`/`XOR` 3 オペランド・`NOT` 2 オペランドの bytes）
* [ ] ASM error（`AND r1, r2` / `NOT r1, r2, r3` が `AsmError`）
* [ ] CPU execute（`AND`/`OR`/`XOR`/`NOT` の結果）
* [ ] Z flag（結果==0 で true）
* [ ] r0（`AND r0, ...` で r0=0 維持）
* [ ] 32bit mask（`NOT` で上位ビット mask）
* [ ] disasm（4 命令の文字列化・unknown は `DW`）
* [ ] opcode 整合（CPU `OP_*` と ASM `_OPCODES` の値一致）
* [ ] Input integration（押下/非押下で分岐）
* [ ] ROM target integration（ROM から fetch/execute）
* [ ] existing tests（Hello World / ram_selftest / fib / legacy / Input / ROM / Program Target / unknown=halt 不変）

## 4. 検証予定

* [ ] `python -m pytest tests/`（全通過・新規テスト込み）
* [ ] bitwise simple program（`AND`/`OR`/`XOR`/`NOT` 手動確認）
* [ ] Input bit 判定 program（キーマスク → 分岐）
* [ ] ROM target bitwise program（ROM から fetch/execute）

## 5. 完了条件

* [x] Bitwise 命令仕様が明確（opcode / format / 動作 / Z / r0 / 32bit mask）
* [x] opcode 互換が守れる（既存 0x00–0x0A 不変・0x0B–0x0E 追加・0xFF 予約）
* [x] CPU / ASM / disasm の変更点が明確（3 か所追記・整合テストで担保）
* [x] 次の実装（`PATCH_AK32_BITWISE_INSTRUCTIONS_V08` 実装）へ進める
