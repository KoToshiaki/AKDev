# PATCH_AK32_INSTRUCTION_EXPANSION_V08 — ROADMAP（設計資料・親計画）

> v0.8（Device Expansion & Connection Validation）の次パッチ候補。AK32 ISA 拡張の**親設計**。
> 本書は設計のみ。**実装・テスト追加・CPU 命令追加・ASM 変更・opcode 変更・既存挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`（§4-D opcode 単一化 / §5-#8）。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_PROGRAM_TARGET_ROM_V08` 完了（`python -m pytest tests/` 1080 passed）。

> **重要な方針**: 本パッチは命令を一気に全部足さない。**親設計（本書）で全体像を固め、実装は小さな子パッチに分割**する。
> 最初の実装は `PATCH_AK32_BITWISE_INSTRUCTIONS_V08`（AND/OR/XOR/NOT）に限定する。CALL/RET/stack は別パッチへ。

---

## 1. 目的

- AK32 にゲーム runtime・複雑処理へ進むための命令を整理し、**どれを・どの順序で・どう実装するか**を確定する。
- Input の bit 判定に必要な **`AND`** 系（bitwise）を最優先候補にする。
- 条件分岐の強化（`BNE` / `BEQZ` / `BNEZ`）を整理する。
- サブルーチン用の `CALL` / `RET` / stack を**設計だけ**丁寧に整理する（実装は後続）。
- opcode 表（現状 3 箇所に重複）と ASM 表記・instruction format を 1 か所で見渡せるよう整理する。
- **今回は設計のみ**。実装・既存挙動変更・opcode 変更はしない。

### スコープ（明確化）

ISA 拡張の全体像・opcode 設計・format・ASM 構文・CPU 実装方針・stack/CALL/RET 設計・段階分割案・テスト方針まで。
実際の命令実装は子パッチ。`ORG`/section/linker、Timer/VRAM/GPIO、game runtime、HDL/FPGA は対象外。

---

## 2. 現在の到達点

- Input device 実装済み。**Input は既存 `LD r, [rs]` で読める**（MMIO・`IN` 命令不要）。
- ROM/program target 実装済み。**ROM target で ROM base から fetch できる土台**がある（reset_pc=rom.base）。
- ただし **Input の bit 判定（特定ビットが立っているか）には bitwise `AND` が無い**ため、現状はマスク判定ができない。
- 現在の条件分岐は **`BEQ rs, rt, rel8`（等値のみ）** と **`JMP imm16`（絶対）**。`BNE` / ゼロ判定分岐は無い。
- **stack / SP / `CALL` / `RET` は無い**（`MemoryLayout.stack_top` フィールドはあるが未使用。GAME16=0xBFFF / circuit_compat・legacy=None）。
- ASM に **`ORG` / section / linker は無い**（2-pass・ラベル対応のみ）。
- 現在 **11 命令**（opcode 0x00–0x0A）。**opcode 表は 3 箇所に重複**（§6）。空き opcode は 0x0B–0xFE（§3 で確認）。

---

## 3. 現在の AK32 命令仕様（実コード確認）

`core/cpu.py` / `asm/asm.py` / `core/runtime.py:disasm` を読んで確認した現行仕様。

### 命令フォーマット（32-bit 固定長・little-endian 出力）

```
bits 31..24  opcode
bits 23..16  rd / rs1   （宛先 or 比較レジスタ1）
bits 15..8   rs / rs2   （ソース or 比較レジスタ2）
bits  7..0   rt / imm8 / rel8
bits 15..0   imm16      （LDI / JMP のみ）
```

### 命令一覧・opcode

| opcode | mnemonic | format | 動作 | Z 更新 |
|---|---|---|---|---|
| 0x00 | `NOP` | — | 何もしない | — |
| 0x01 | `HALT` | — | 停止。`pc -= 4`（PC を HALT に保持） | — |
| 0x02 | `LDI rd, imm16` | imm16 | `rd = zero_ext(imm16)` | ✔（imm16==0） |
| 0x03 | `OUT [rd], rs` | R | `bus.write(regs[rd], regs[rs])`・BusError→halt | — |
| 0x04 | `ADD rd, rs, rt` | R(3) | `rd = rs + rt`（rt=bits7..0） | ✔ |
| 0x05 | `SUB rd, rs, rt` | R(3) | `rd = rs - rt` | ✔ |
| 0x06 | `LD rd, [rs]` | R | `rd = bus.read(regs[rs])`・BusError→halt | ✔ |
| 0x07 | `ST [rd], rs` | R | `bus.write(regs[rd], regs[rs])`・BusError→halt | — |
| 0x08 | `JMP imm16` | imm16 | `pc = imm16`（絶対・16bit） | — |
| 0x09 | `BEQ rs1, rs2, rel8` | branch | `if regs[rs1]==regs[rs2]: pc += signed(rel8)*4` | — |
| 0x0A | `ADDI rd, rs, imm8` | imm8 | `rd = rs + imm8`（unsigned 8bit） | ✔ |

### 確認した不変条件（tests で保証）

- **register 数 16**（r0–r15）。**r0 はハードワイヤ 0**（`_set_reg` が idx==0 を無視）。書込みは `& 0xFFFFFFFF`（32bit wrap）。
- **PC 更新**: `tick()` が fetch 後に `pc += 4`。分岐/JMP はその後で上書き。`HALT` は `pc -= 4` で自留。
- **`BEQ` 分岐条件**: rs1==rs2 のとき `pc += signed(rel8)*4`（rel8 は pc_after_branch=instr_pc+4 基準・語単位・-128..127）。Z は使わない。
- **`JMP` address 幅**: imm16（0x0000–0xFFFF）。絶対。
- **`LD`/`ST` の address 指定**: レジスタ間接 `[rs]` / `[rd]`（regs の値がアドレス）。
- **`OUT`**: `[rd]` 間接・`ST` と同義系（MMIO 書込み）。
- **Z flag** は LDI/ADD/SUB/LD/ADDI が結果==0 で更新。
- **unknown opcode → halt**（`test_unknown_opcode_halts` が **0xFF** で検証 → 0xFF は将来も「未割当=halt」を保つべき）。
- assembler 構文: 大文字小文字非依存（`mnem.upper()`）、`#` 以降コメント、`r0`–`r15`、`[rN]`、imm は `int(token,0)`（10/16 進）、`label:`、`JMP/BEQ` はラベル可。
- ADD/SUB/ADDI は **3 オペランド**（rt は bits7..0 のレジスタ番号 or imm8）。

### サンプル（既存・`src/fib.asm`）

ADD/ST/ADDI/BEQ/JMP のループ。`ADD r1, r2, r0`（r0=0 を使ってコピー）など、**r0 をスクラッチ 0 として活用する慣習**がある。

---

## 4. 追加命令候補

### 低リスク・優先候補（ALU・bitwise）

| mnemonic | format 案 | 動作 |
|---|---|---|
| `AND rd, rs, rt` | R(3) | `rd = rs & rt` |
| `OR  rd, rs, rt` | R(3) | `rd = rs | rt` |
| `XOR rd, rs, rt` | R(3) | `rd = rs ^ rt` |
| `NOT rd, rs` | R(2) | `rd = ~rs & 0xFFFFFFFF` |
| `SHL rd, rs, imm8` | imm8 | `rd = (rs << imm8) & 0xFFFFFFFF` |
| `SHR rd, rs, imm8` | imm8 | `rd = rs >> imm8`（論理右）|

### Input 処理に効く候補

- `ANDI rd, rs, imm8` / `ORI rd, rs, imm8` / `XORI rd, rs, imm8`（imm8 マスク。8bit キーマスクに十分）。
- `BNE rs1, rs2, rel8`（不等分岐）。
- `BEQZ rs, rel8` / `BNEZ rs, rel8`（ゼロ/非ゼロ分岐＝`AND` 結果の判定に直結）。

### 制御構造に効く候補

- `CALL addr` / `RET` / `PUSH rs` / `POP rd`（stack 設計が必要。§10）。

### 将来候補

- `CMP ra, rb`（flag 拡張が要る）/ `BLT` / `BGT` / `LUI`（上位 16bit ロード＝32bit 即値合成）/ `IN`（便利命令）/ `OUTI` / `MUL`。

### 重要な判断

- **`IN` は Input 実装に必須ではない**（Input は `LD` で読める）。`IN` は便利命令として**後続**。
- **最初の実装は `CALL/RET`（stack 必要）より、`AND`/`OR`/`XOR`/`NOT` の ALU 命令を優先**する。
  理由: stack 設計不要・memory layout 非依存・既存 ADD/SUB と同 format で実装しやすい・既存互換を壊しにくい。

### format に関する注記（prompt の 2 オペランド案 vs 既存 3 オペランド）

prompt の例は `AND r2, r1`（2 オペランド・`r2 &= r1`）だが、**既存 ALU（ADD/SUB）は 3 オペランド `rd, rs, rt`**。
本設計は **3 オペランド `AND rd, rs, rt` を推奨**する（format/encode/disasm を ADD/SUB と完全共通化でき、新 format を増やさない）。
2 オペランド `AND rd, rs`（=`rd &= rs`）も可能だが ALU 系の一貫性が崩れるため非推奨。`r2 &= r1` は `AND r2, r2, r1` で表現できる。

---

## 5. 最初に実装すべき命令セット案（段階分割）

| Phase | 子パッチ案 | 命令 | 主な理由 |
|---|---|---|---|
| 0（任意・推奨） | `PATCH_AK32_OPCODE_TABLE_V08` | （命令追加なし） | opcode 3 重定義を `core/opcodes.py` へ単一化。§6・review §4-D「必須級」 |
| 1 | `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` | `AND` `OR` `XOR` `NOT` | Input bit 判定直結・stack 不要・既存互換 |
| 2 | `PATCH_AK32_SHIFT_IMM_BITWISE_V08` | `SHL` `SHR` `ANDI` `ORI`（`XORI`） | マスク/シフト・imm8 format 流用 |
| 3 | `PATCH_AK32_BRANCH_EXPANSION_V08` | `BNE` `BEQZ` `BNEZ` | 条件分岐強化・`AND`+ゼロ判定の組合せ |
| 4 | `PATCH_AK32_STACK_CALL_RET_V08` | `PUSH` `POP` `CALL` `RET` | subroutine・SP/stack 設計が要るため後回し |
| 5 | `PATCH_AK32_CONVENIENCE_INSTR_V08` | `IN` `OUTI` `LUI`（`CMP`/`MUL`）| 便利命令・32bit 即値合成等 |

> Phase 0 は「命令を増やさず真実源を 1 つにする」リファクタ。Phase 1 以降の整合コストを下げる。
> review は Phase 0 を「命令拡張前に必須級」と位置づける。最小で進めたい場合は Phase 1 を先に単独でもよいが、その場合 opcode を 3 箇所に追記する点を許容する。

---

## 6. opcode 設計方針

### 現在の割当と空き

- 使用済み: **0x00–0x0A**（11 命令）。
- 空き: **0x0B–0xFE**（244 個）。`0xFF` は `test_unknown_opcode_halts` が「未割当=halt」検証に使用 → **0xFF は割り当てない**（予約: guaranteed-unknown）。
- opcode は **8bit**（bits 31..24）。命令長は **32bit 固定**。

### 割当案（Phase 1）

| opcode | mnemonic |
|---|---|
| 0x0B | `AND rd, rs, rt` |
| 0x0C | `OR  rd, rs, rt` |
| 0x0D | `XOR rd, rs, rt` |
| 0x0E | `NOT rd, rs` |

（Phase 2 以降は 0x0F, 0x10, … と末尾追記。）

### 不変条件

- **既存 opcode（0x00–0x0A）は変更禁止**。既存 binary は同じ bytes が同じ挙動。
- 新命令は**空き opcode に追記のみ**（末尾連番）。
- **opcode 表は現状 3 箇所に重複**（真実源の三重管理）:
  1. `core/cpu.py` — `OP_*` 定数 + `_execute` の decode。
  2. `asm/asm.py` — `_OPCODES` dict（**独自リテラル**）+ 各 mnemonic の encode。
  3. `core/runtime.py:disasm` — decode（`AK32Part.OP_*` を参照するので定数値は共有、ただし mnemonic 文字列は独自）。
- → 命令追加時は **最低でも cpu.py / asm.py の 2 箇所、表示も含めると 3 箇所**を整合させる必要がある。
  **Phase 0 で `core/opcodes.py`（mnemonic↔opcode↔operand 形式の単一テーブル）へ集約**すると、以後の追加が 1 箇所で済む（推奨）。

---

## 7. instruction format 方針

新 format を増やさず、**既存 4 形式に寄せる**:

- **R-type 3 オペランド**（ADD/SUB と同型）: `AND/OR/XOR rd, rs, rt` → `op<<24 | rd<<16 | rs<<8 | rt`。
- **R-type 2 オペランド（unary）**: `NOT rd, rs` → `op<<24 | rd<<16 | rs<<8`（bits7..0=0）。
- **imm8 型**（ADDI と同型）: `SHL/SHR/ANDI/ORI rd, rs, imm8` → `op<<24 | rd<<16 | rs<<8 | imm8`。
- **branch 型**（BEQ と同型）: `BNE rs1, rs2, rel8`。`BEQZ/BNEZ rs, rel8` は rs2 スロットを未使用(0)にする 2 オペランド branch。
- **jump/stack**（後続）: `CALL addr`（JMP と同型 imm16）/ `RET`（オペランドなし）/ `PUSH rs` `POP rd`（R 2 オペランド）。

shift 量を「1 固定（`SHL rd, rs`）」にする案もあるが、imm8 型に乗せて任意シフト（`SHL rd, rs, imm8`）の方が汎用。**imm8 型を推奨**。

---

## 8. ASM 構文方針

既存の `asm/asm.py` 慣習に完全準拠（新規構文は足さない）:

- 大文字小文字非依存（`tokens[0].upper()`）。`#` 以降コメント。空行/`label:` スキップ。
- register `r0`–`r15`（`_parse_reg`）。間接 `[rN]`（`_parse_deref`）。imm は `_parse_imm`（`int(token,0)`・10/16 進・ビット幅検証）。
- 新命令の operand 数チェックを既存同様に `len(args)` で行い、`AsmError(lineno, ...)` を投げる。
- bitwise はラベル不要（branch のみラベル/rel8 解決 `_resolve_rel8` を流用）。
- **disasm 対応**: `core/runtime.py:disasm` に新 mnemonic の分岐を追加（trace/Run Status 表示のため）。未対応だと `DW 0x...` 表示になるだけで実行は問題ないが、整合のため追加する。

サンプル（Phase 1 後の想定・既存構文に準拠）:

```asm
    LDI r1, 0x0110     # Input MMIO base（例）
    LD  r2, [r1]       # キー状態を読む
    LDI r3, 0x10       # A ボタンのビットマスク
    AND r2, r2, r3     # r2 = 押下ビットのみ
    BEQ r2, r0, no_a   # 0 なら A は押されていない
```

---

## 9. CPU 実装方針（`core/cpu.py`）

- `_execute(instr)` の `elif` チェーンに新 opcode 分岐を追加（既存分岐は不変）。
- ALU 系は ADD/SUB と同じ抽出（`rd=bits23..16`, `rs=bits15..8`, `rt=bits7..0`）。
  - `AND`: `self._set_reg(rd, self._regs[rs] & self._regs[rt])`、Z は結果==0 で更新（ALU 命令の慣習に合わせる）。
  - `OR`/`XOR` 同様。`NOT`: `self._set_reg(rd, (~self._regs[rs]) & 0xFFFFFFFF)`、Z 更新。
- **register write は `_set_reg` 経由**（r0 ハードワイヤ・32bit mask を保証）。
- **PC 更新は不変**（ALU は分岐しないので `tick()` の `pc += 4` のまま）。
- **flag**: 現状 Z のみ。bitwise も Z を更新する設計（ゼロ判定分岐 BEQZ/BNEZ と相性が良い）。`CMP`/符号比較は将来 flag 拡張時に検討（今回やらない）。
- **branch（Phase 3）**: BEQ と同様に `pc += signed(rel8)*4`。BEQZ/BNEZ は片側レジスタとゼロ比較。
- **unknown opcode の扱いは不変**（else→halt）。新 opcode を足しても 0xFF 等は halt のまま。
- **見るべき内部状態（test）**: `regs()` / `z_flag()` / `pc()` / `halted()`。

---

## 10. stack / CALL / RET 方針（設計のみ・実装は後続）

CALL/RET は最も影響が大きいため、**今回は設計を残すだけ**（Phase 4 / `PATCH_AK32_STACK_CALL_RET_V08`）。

検討事項と推奨:

- **SP（stack pointer）**: 専用 SP レジスタを増やすか、既存 16 レジスタの 1 本（例 `r15`）を SP 規約にするか。
  - 推奨: まずは **`r15` を SP とする規約**（レジスタ追加・encode 変更なしで済む）。専用 SP は ISA 変更が大きい。
- **stack 領域**: RAM 上に置く。`MemoryLayout.stack_top` を初期 SP に使う（GAME16=0xBFFF）。
  - circuit_compat/legacy は `stack_top=None` → CALL/RET を使う構成では layout 側に stack_top を与えるか、プログラム側で SP を初期化する規約にする。
- **CALL addr**: `push(pc_return)` してから `pc = addr`。戻りアドレスは「CALL の次命令」。
- **RET**: `pc = pop()`。register-indirect jump（PC を pop 値へ）になる。
- **PUSH rs / POP rd**: `SP -= 4; mem[SP] = rs` / `rd = mem[SP]; SP += 4`（下方成長の例）。成長方向は設計時に確定。
- **overflow/underflow**: SP が stack 領域を外れたら BusError（既存 Bus の範囲外 read/write→halt）で自然に止まる。明示チェックは任意。
- **ROM 実行時**: ROM は read-only なので **stack は必ず RAM**（program target=ROM でも RAM を作業領域に残す前提＝`PATCH_PROGRAM_TARGET_ROM_V08` の方針と整合）。
- **今回の最初の実装に CALL/RET は含めない**（Phase 1 は bitwise のみ）。

---

## 11. Input bit 判定のサンプル方針

Phase 1（bitwise）の実装時に、Input + 新命令のサンプル ASM を **test または example** として追加する:

```asm
    LDI r1, 0x0110     # Input base（実際の base は Address Map に合わせる）
    LD  r2, [r1]       # KEY_STATE
    LDI r3, 0x10       # A ボタン bit（InputPart のキー割当に合わせる）
    AND r2, r2, r3
    BEQ r2, r0, no_a   # 0 → 非押下
    # ... A 押下時の処理 ...
no_a:
    HALT
```

- 既存 `InputPart`（`set_keys`）でキーを立て、`AND`+`BEQ` で判定できることを test 化する。
- example として `src/` か `tests/test/` に置くかは実装時に決める（既存 `tests/test/*.asm` の流儀に合わせる）。

---

## 12. ROM target との関係

- 新命令は**命令 fetch（`bus.read(pc)`）で実行**されるため、RAM target でも ROM target でも同様に動く（命令の置き場所に依存しない）。
- program target は**既定 RAM のまま**（本パッチは ISA だけ・target は変えない）。
- 実装時に **ROM target で bitwise 命令が fetch/execute できる test** を 1 本足す（`PATCH_PROGRAM_TARGET_ROM_V08` のテスト流儀＝override で ROM 配置 → `set_program_target("rom")` → write → run）。
- **既存の ROM target テストを壊さない**（命令追加は既存 opcode を変えないため影響しないはず）。

---

## 13. 既存互換方針（必須）

- **既存 opcode（0x00–0x0A）は変更しない**。`0xFF`=未割当(halt) を保つ。
- 既存 ASM はそのまま assemble でき、既存 binary は同じ挙動。
- Hello World / ram_selftest / fib / legacy mode を壊さない。
- Input / ROM / program target / address map editor のテストを壊さない。
- `test_unknown_opcode_halts`（0xFF）が通り続ける。
- `python -m pytest tests/` 全通過。

---

## 14. 実装スコープ案（次に実装するなら・安全な範囲）

**Phase 1 = `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` のみ**を推奨:

- `core/cpu.py`: `OP_AND=0x0B` / `OP_OR=0x0C` / `OP_XOR=0x0D` / `OP_NOT=0x0E` 定数 + `_execute` 分岐（Z 更新・`_set_reg` 経由）。docstring 更新。
- `asm/asm.py`: `_OPCODES` に 4 命令追加 + encode 分岐（AND/OR/XOR は 3 オペランド・NOT は 2 オペランド・operand 数チェック）。docstring 更新。
- `core/runtime.py:disasm`: 4 命令の表示分岐追加。
- tests 追加（§15）。Input bit 判定サンプル test・ROM target fetch/execute test。
- `PATCH_..._CHECKLIST.md` 更新。`CHECKLIST8.md` 最小追記。
- **既存互換維持**。

やらないこと: Phase 2 以降（shift/imm/branch/stack/convenience）・opcode 単一化リファクタ（Phase 0 は任意別パッチ）・CALL/RET/stack・ORG/linker・新 device・game runtime。

> 代替: opcode 三重管理が気になるなら **Phase 0（`PATCH_AK32_OPCODE_TABLE_V08`）を先に**実施し、その上で Phase 1 を行うと追加が 1 箇所で済む。

---

## 15. テスト方針（実装時に追加するテスト）

- ASM が `AND r1, r2, r3` / `OR` / `XOR` / `NOT r1, r2` を assemble できる（encode bytes 検証）。
- ASM の operand 数エラー（例: `AND r1, r2` → AsmError）。
- CPU が `AND`/`OR`/`XOR`/`NOT` を実行できる（`regs()` 検証）。
- register が 32bit mask される（`NOT` で上位ビット・`& 0xFFFFFFFF`）。
- Z flag が結果==0 で立つ（bitwise でも）。
- r0 宛先は 0 のまま（`AND r0, ...`）。
- PC が 1 命令ぶん（+4）進む（分岐しない）。
- **unknown opcode（0xFF）が引き続き halt**（`test_unknown_opcode_halts` 不変）。
- Input bit 判定サンプル（`LD`+`AND`+`BEQ`）が期待どおり分岐する。
- ROM target で bitwise 命令が fetch/execute される。
- disasm が新命令を正しく文字列化する。
- 既存 Hello World / ram_selftest / fib / legacy / Input / ROM / Program Target テストが壊れない。
- `python -m pytest tests/` 全通過。

---

## 16. 今回やらないこと

- 実装 / CPU 命令追加 / ASM 変更 / opcode 変更 / tests 追加
- `CALL` / `RET` / `PUSH` / `POP` / stack 実装
- `BNE` / `BEQZ` / `BNEZ` / shift / immediate bitwise の実装
- opcode 単一化リファクタ（`core/opcodes.py`）の実装
- `ORG` / section / linker
- Timer / VRAM / GPIO / Storage 実装
- game runtime 実装
- HDL / FPGA export
- 既存挙動変更 / commit / push

---

## 17. 次に続くパッチ（候補順）

1. `PATCH_AK32_OPCODE_TABLE_V08`（任意・推奨先行 — opcode 三重管理を `core/opcodes.py` へ単一化・命令追加なし）
2. `PATCH_AK32_BITWISE_INSTRUCTIONS_V08`（**最初の実装** — `AND`/`OR`/`XOR`/`NOT`）
3. `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL`/`SHR`/`ANDI`/`ORI`）
4. `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE`/`BEQZ`/`BNEZ`）
5. `PATCH_AK32_STACK_CALL_RET_V08`（`PUSH`/`POP`/`CALL`/`RET` + SP/stack）
6. `PATCH_TIMER_DEVICE_V08` / `PATCH_VRAM_DEVICE_V08`
7. `PATCH_GAME_RUNTIME_MINIMAL_V08`（ROM + Input + Timer + VRAM の最小ループ）
8. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> 本書（`PATCH_AK32_INSTRUCTION_EXPANSION_V08`）は**親設計**。実装は 2.（Bitwise）から小さく始め、stack/CALL/RET は 5. に分離する。
> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: Diagnostics Panel / Project Validation / **opcode 単一定義化（命令拡張前に必須級）** / テストフィクスチャ整理。
