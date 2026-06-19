# PATCH_AK32_BITWISE_INSTRUCTIONS_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の次パッチ候補。親設計 `PATCH_AK32_INSTRUCTION_EXPANSION_V08` の
> **最初の子パッチ（Phase 1）**。AK32 に bitwise 命令 `AND` / `OR` / `XOR` / `NOT` を追加する詳細設計。
> 本書は設計のみ。**実装・CPU 命令追加・ASM 変更・opcode 変更・テスト追加・既存挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md` / `PATCH_AK32_INSTRUCTION_EXPANSION_V08_ROADMAP.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_AK32_INSTRUCTION_EXPANSION_V08`（親設計）完了（`python -m pytest tests/` 1080 passed）。

> **対象は 4 命令に限定**: `AND rd, rs, rt` / `OR rd, rs, rt` / `XOR rd, rs, rt` / `NOT rd, rs`。
> `CALL`/`RET`/`PUSH`/`POP`/stack/shift/immediate bitwise/branch 拡張/`IN` は対象外（後続パッチ）。

---

## 1. 目的

- AK32 に bitwise 命令 `AND` / `OR` / `XOR` / `NOT` を追加する。
- Input の **bit mask 判定**（特定キーが押されているかの判定）を可能にする（`LD`+`AND`+`BEQ`）。
- 4 命令を **CPU（`core/cpu.py`）/ ASM（`asm/asm.py`）/ disasm（`core/runtime.py`）** の 3 か所に対応させる。
- 既存 opcode（0x00–0x0A）を変更せず、**空き opcode 0x0B–0x0E に末尾追加**する。
- 既存 ASM・既存 binary・既存テストを壊さない（特に `test_unknown_opcode_halts`=0xFF）。
- **今回は設計のみ**。実装・既存挙動変更はしない。

### スコープ（明確化）

`AND`/`OR`/`XOR`（3 オペランド R-type）+ `NOT`（2 オペランド R-type）の CPU 実行・ASM encode・disasm 表示・テスト。
shift / immediate bitwise / branch 拡張 / stack / CALL/RET / IN / opcode 単一化リファクタは対象外。

---

## 2. 現在の到達点（実コード確認）

- **Input は既存 `LD r, [rs]` で読める**（MMIO・`IN` 不要）。Input base は encounter 順で UART=0x0100 のとき **Input=0x0110**（`tests/test_input_device_v08.py` 確認）。
- **Input の bit 判定には `AND` が必要**（現状 bitwise が無くマスク判定不可）。
- **ROM target で ROM base から新命令を fetch できる土台**がある（`PATCH_PROGRAM_TARGET_ROM_V08`・命令は `bus.read(pc)` で fetch）。
- 現在 **11 命令**（opcode **0x00–0x0A**）。`core/cpu.py` の docstring・`asm/asm.py` の `_OPCODES`・`core/runtime.py:disasm` で確認。
- **空き opcode は 0x0B–0xFE**。`0xFF` は `test_unknown_opcode_halts`（`tests/test_cpu_v04.py`）が「未割当=halt」検証に使用 → **予約（割り当てない）**。
- **opcode 知識は 3 か所**:
  - `core/cpu.py` — `OP_*` 定数 + `_execute()` の decode（else→halt）。
  - `asm/asm.py` — `_OPCODES` dict（独自リテラル）+ 各 mnemonic の encode。
  - `core/runtime.py:disasm` — 表示用 decode（`AK32Part.OP_*` 定数を参照・mnemonic 文字列は独自）。
- **ADD/SUB は 3 オペランド R-type**: `op<<24 | rd<<16 | rs<<8 | rt`（rt は bits7..0 のレジスタ番号）。
- **Z flag** あり（LDI/ADD/SUB/LD/ADDI が結果==0 で更新）。**r0 はハードワイヤ 0**（`_set_reg` が idx==0 を無視）。書込みは `& 0xFFFFFFFF`。
- **命令長 32bit 固定**・little-endian 出力。PC は fetch 後 `+4`（分岐命令だけ上書き）。

---

## 3. 対象命令仕様

| 命令 | opcode | format | 動作 | Z flag |
|---|---:|---|---|---|
| `AND rd, rs, rt` | `0x0B` | R-type 3 operand | `rd = (rs & rt) & 0xFFFFFFFF` | 結果==0 で更新 |
| `OR  rd, rs, rt` | `0x0C` | R-type 3 operand | `rd = (rs \| rt) & 0xFFFFFFFF` | 結果==0 で更新 |
| `XOR rd, rs, rt` | `0x0D` | R-type 3 operand | `rd = (rs ^ rt) & 0xFFFFFFFF` | 結果==0 で更新 |
| `NOT rd, rs`     | `0x0E` | R-type 2 operand | `rd = (~rs) & 0xFFFFFFFF` | 結果==0 で更新 |

方針:

- **`AND`/`OR`/`XOR` は既存 `ADD`/`SUB` と同じ 3 オペランド形式**（encode/decode/disasm を完全共通化）。
- **`NOT` は 2 オペランド形式**（`rd, rs`・bits7..0 は 0）。`OUT`/`LD`/`ST` と同じ「rs スロットだけ使う」形に倣う。
- **2 オペランド `AND rd, rs`（=`rd &= rs`）は採用しない**。`rd &= rs` は **`AND rd, rd, rs`** で表現する（既存の `ADD r1, r2, r0` で r0 をスクラッチに使う慣習と整合）。
- **`r0` への書き込みは無視**（`_set_reg` 経由・既存どおり）。
- **結果は 32bit mask**（特に `NOT` は `~` の符号拡張を `& 0xFFFFFFFF` で抑える）。
- **Z flag は結果が 0 なら true**（既存 ALU 命令の慣習に合わせる。ゼロ判定分岐 `BEQZ`/`BNEZ` を将来導入する際に相性が良い）。

---

## 4. opcode 方針

必須方針:

- **既存 opcode 0x00–0x0A は変更しない**（既存 binary は同 bytes＝同挙動）。
- **`0xFF` は unknown opcode 用に予約**し、割り当てない（`test_unknown_opcode_halts` を保つ）。
- 新 opcode は **0x0B–0x0E**（末尾連番）。
- CPU / ASM / disasm の **3 か所を揃える**必要がある（真実源の三重管理）。

### 今回の進め方（3 か所追記 vs opcode 単一化先行）

- **今回の `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` は命令追加に集中**し、`core/cpu.py` / `asm/asm.py` / `core/runtime.py:disasm` の **3 か所追記**で進める。
- **opcode 単一化（`core/opcodes.py`）は今回やらない**。やるなら**別パッチ `PATCH_AK32_OPCODE_TABLE_V08`**（先行 or 後続）として扱う。
  - 4 命令だけなら 3 か所追記のコストは小さく、先に単一化リファクタを挟むより素早く安全に進められる。
  - ただし **3 か所がズレない保証をテストで担保**する（§13 — CPU 実行・ASM encode・disasm 文字列の整合テスト、特に opcode 定数値が CPU/ASM で一致すること）。
- 親設計（`PATCH_AK32_INSTRUCTION_EXPANSION_V08`）は単一化を「任意先行・推奨」と記録済み。本子パッチでは**単一化なしで進める判断**を明記する。

---

## 5. instruction format 方針

前提（現行エンコード・変更なし）:

```
bits 31..24  opcode
bits 23..16  rd
bits 15..8   rs
bits  7..0   rt / imm8
```

- 32bit 固定長・little-endian 出力（`struct.pack('<I', word)`）。
- **`AND`/`OR`/`XOR`**（3 オペランド）: `op << 24 | rd << 16 | rs << 8 | rt`。
- **`NOT`**（2 オペランド）: `op << 24 | rd << 16 | rs << 8`（**bits 7..0 = 0**）。
- 新しい format は増やさない（既存 R-type の枠に収める）。

エンコード例（参考・実装時に検証する想定値）:

- `AND r1, r2, r3` → `0x0B_01_02_03`
- `OR  r1, r2, r3` → `0x0C_01_02_03`
- `XOR r1, r2, r3` → `0x0D_01_02_03`
- `NOT r1, r2`     → `0x0E_01_02_00`

---

## 6. ASM 構文方針（`asm/asm.py`）

対象構文（既存慣習に完全準拠・新規構文なし）:

```asm
AND r1, r2, r3
OR  r1, r2, r3
XOR r1, r2, r3
NOT r1, r2
```

確認項目:

- **大文字小文字非依存**（`tokens[0].upper()`）。`#` 以降コメント（`_strip_comment`）。空行/`label:` スキップ。
- **register parse** は `_parse_reg`（`r0`–`r15`）。間接 `[rN]` は使わない（bitwise はレジスタのみ）。
- **operand 数チェック**: `AND`/`OR`/`XOR` は `len(args)==3`、`NOT` は `len(args)==2`。不一致は既存同様 `AsmError(lineno, "... requires N operands, got M")`。
- **encode**: `_OPCODES` に `'AND':0x0B, 'OR':0x0C, 'XOR':0x0D, 'NOT':0x0E` を追加し、pass 2 に 4 命令の `elif` 分岐を追加。3 オペランドは ADD/SUB の encode をそのまま流用、`NOT` は rs スロットのみ。
- **ラベル処理への影響なし**（pass 1 は mnemonic を `_OPCODES` で認識して PC を +4 するだけ。bitwise 追加で既存ラベル解決は不変）。
- **既存 ASM を壊さない**（既存 mnemonic の分岐は不変・新 mnemonic は追加のみ）。

---

## 7. CPU 実装方針（`core/cpu.py`）

- opcode 定数追加: `OP_AND = 0x0B` / `OP_OR = 0x0C` / `OP_XOR = 0x0D` / `OP_NOT = 0x0E`。
- `_execute()` の `elif` チェーンに 4 分岐を追加（既存分岐は不変）。抽出は ADD/SUB と同じ（`rd=bits23..16`, `rs=bits15..8`, `rt=imm8=bits7..0`）:
  - `AND`: `self._set_reg(rd, self._regs[rs] & self._regs[rt])`、`self._z = (result32 == 0)`。
  - `OR` / `XOR`: 同様（`|` / `^`）。
  - `NOT`: `self._set_reg(rd, (~self._regs[rs]) & 0xFFFFFFFF)`、`self._z = (result32 == 0)`（rt スロットは無視）。
- **`_set_reg()` 経由で書き込む**（r0 保護・32bit mask を保証）。
- **PC 更新は通常どおり +4**（bitwise は分岐しない）。
- **unknown opcode は従来どおり halt**（else 節不変。0x0F 以降・0xFF は引き続き halt）。
- docstring（opcode 表）を 4 命令ぶん更新。
- 見るべき内部状態（test）: `regs()` / `z_flag()` / `pc()` / `halted()`。

---

## 8. disasm 方針（`core/runtime.py:disasm`）

- 既存表示形式に合わせて 4 命令の分岐を追加:
  - `AND` → `f"AND r{rd}, r{rs}, r{rt}"`（ADD/SUB と同形）。
  - `OR`  → `f"OR r{rd}, r{rs}, r{rt}"`。
  - `XOR` → `f"XOR r{rd}, r{rs}, r{rt}"`。
  - `NOT` → `f"NOT r{rd}, r{rs}"`（2 オペランド表示）。
- `AK32Part.OP_*` 定数を参照（CPU と同じ真実源・新定数を使う）。
- **unknown opcode 表示を壊さない**（末尾の `DW 0x{word:08x}` フォールバックは不変）。
- Trace / Run Status 上で新命令が `DW ...` ではなく mnemonic 表示されることを確認（step trace の `instruction` 文字列）。

---

## 9. Input bit 判定テスト方針

Input device と bitwise を統合するサンプル（base は Address Map に依存。UART あり構成で Input=0x0110）:

```asm
    LDI r1, 0x0110     # Input KEY_STATE base
    LD  r2, [r1]       # キー状態を読む
    LDI r3, 0x10       # A ボタン bit（InputPart: bit4 = A）
    AND r2, r2, r3     # 押下ビットのみ残す
    BEQ r2, r0, no_a   # 0 なら A 非押下
    LDI r4, 1          # 押下: r4 = 1
    HALT
no_a:
    LDI r4, 0          # 非押下: r4 = 0
    HALT
```

テスト方針:

- `InputPart.set_keys(0x10)`（A 押下・bit4）で **押下時 r4==1**、`set_keys(0x00)` で **非押下時 r4==0** の**両方**をテストする。
- `LD` で Input を読む → `AND` で bit 判定 → `BEQ` で分岐、の一連を MainWin 経由（`write_program`→`_do_run`）または CPU 単体（`tests/test_cpu_v04.py` 流儀の手組み binary）で検証。
- **Address Map の Input base**: 自動配置（encounter 順 UART 0x0100 / Input 0x0110）を使う。base が変わる構成では override で固定する案も可（テストの安定性優先）。
- 単体 CPU テストでは `InputPart` を bus に attach し base を固定（例 0x0110）して検証するのが簡単。

---

## 10. ROM target 統合テスト方針

- `PATCH_PROGRAM_TARGET_ROM_V08` のテスト流儀に倣う（`tests/test_program_target_rom_v08.py`）:
  - ROM を override で **base 0x0000** に配置・RAM を縮小（overlap 回避）。
  - `set_program_target("rom")` → bitwise を含むプログラムを `write_program()` → `_do_run()`。
  - CPU が **ROM から fetch** して bitwise を実行することを確認（`reset_pc=rom.base`）。
- `AND`/`OR`/`XOR`/`NOT` の**最低 1 つ**を ROM target で実行確認（例: `LDI` で値を入れて `AND`/`NOT` し結果レジスタを検証）。
- **既存 Program Target ROM テストを壊さない**（命令追加は既存 opcode を変えないため影響しないはず）。
- RAM target でも同じ bitwise が動くこと（fetch ベースで置き場所非依存）を最低 1 ケース確認。

---

## 11. 既存互換方針（必須）

- **既存 opcode（0x00–0x0A）は変更しない**。
- 既存 ASM はそのまま assemble でき、既存 binary は同じ挙動。
- **Hello World** / **ram_selftest** / **fib.asm** / **legacy mode** を壊さない。
- **Input tests** / **ROM tests** / **Program Target tests** を壊さない。
- **`test_unknown_opcode_halts`（0xFF）** を壊さない（0xFF は未割当のまま）。
- `python -m pytest tests/` 全通過。

---

## 12. 実装スコープ案（次に実装するなら・安全な範囲）

- `core/cpu.py`: opcode 定数 4 個追加 + `_execute` に 4 命令分岐（`_set_reg`・Z 更新・32bit mask）+ docstring 更新。
- `asm/asm.py`: `_OPCODES` に 4 命令追加 + pass 2 に encode 分岐（operand 数チェック）+ docstring 更新。
- `core/runtime.py`: `disasm` に 4 命令の表示分岐追加。
- tests 追加: `tests/test_ak32_bitwise_instructions_v08.py`（ASM encode / CPU execute / Z / r0 / 32bit mask / disasm / Input 統合 / ROM target 統合 / 既存不変）。
- `PATCH_AK32_BITWISE_INSTRUCTIONS_V08_CHECKLIST.md` 更新・`CHECKLIST8.md` 最小追記。
- **既存互換維持**。

やらないこと: opcode 単一化リファクタ・shift・immediate bitwise・branch 拡張・stack/CALL/RET・IN・新 device・game runtime。

---

## 13. テスト方針（実装時に追加するテスト）

- **ASM encode**: `AND r1, r2, r3` / `OR r1, r2, r3` / `XOR r1, r2, r3` / `NOT r1, r2` の bytes 検証（§5 の例）。
- **ASM operand error**: `AND r1, r2`（3 必要）/ `NOT r1, r2, r3`（2 必要）が `AsmError`。
- **CPU execute**: `AND`/`OR`/`XOR`/`NOT` の結果（既知値で検証）。
- **Z flag**: 結果==0 で `z_flag()` true（例 `AND` で 0、`XOR rx, rx` で 0）。
- **r0 書き込み保護**: `AND r0, r1, r2` で r0 が 0 のまま。
- **32bit mask**: `NOT r1, r2`（r2=0 → r1=0xFFFFFFFF）など上位ビットの mask 確認。
- **PC +4**: bitwise 実行で PC が 1 命令ぶん進む（分岐しない）。
- **disasm**: 4 命令が正しく文字列化される。unknown は `DW ...` のまま。
- **opcode 整合**: CPU の `OP_*` と ASM の `_OPCODES` の値が一致（3 か所ズレ防止）。
- **Input integration**: `LD`+`AND`+`BEQ` で押下/非押下を分岐（§9・両ケース）。
- **ROM target integration**: ROM から bitwise を fetch/execute（§10）。
- **existing tests**: Hello World / ram_selftest / fib / legacy / Input / ROM / Program Target / `test_unknown_opcode_halts` 不変。
- `python -m pytest tests/` 全通過。

---

## 14. 今回やらないこと

- 実装 / CPU 命令追加 / ASM 変更 / opcode 変更 / tests 追加
- opcode 単一化（`core/opcodes.py`）
- shift 命令（`SHL` / `SHR`）
- immediate bitwise（`ANDI` / `ORI` / `XORI`）
- branch 拡張（`BNE` / `BEQZ` / `BNEZ`）
- `CALL` / `RET` / `PUSH` / `POP` / stack
- `IN` 命令
- `ORG` / section / linker
- Timer / VRAM / GPIO 実装
- game runtime 実装
- HDL / FPGA export
- 既存挙動変更 / commit / push

---

## 15. 次に続くパッチ（候補順）

1. **`PATCH_AK32_BITWISE_INSTRUCTIONS_V08`（本パッチ — 最有力・次に実装へ進むならこれ）**
2. `PATCH_AK32_OPCODE_TABLE_V08`（opcode 三重管理を `core/opcodes.py` へ単一化・命令追加なし）
3. `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL` / `SHR` / `ANDI` / `ORI`）
4. `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE` / `BEQZ` / `BNEZ`）
5. `PATCH_AK32_STACK_CALL_RET_V08`（`PUSH` / `POP` / `CALL` / `RET` + SP/stack）
6. `PATCH_TIMER_DEVICE_V08`
7. `PATCH_VRAM_DEVICE_V08`
8. `PATCH_GAME_RUNTIME_MINIMAL_V08`（ROM + Input + Timer + VRAM の最小ループ）

> **次に実装へ進むなら `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` が最有力**。親設計 `PATCH_AK32_INSTRUCTION_EXPANSION_V08` の
> Phase 1 であり、Input bit 判定に直結し、stack 非依存・既存互換で最も低リスク。
> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: opcode 単一定義化（命令拡張を重ねるなら早めに）。
