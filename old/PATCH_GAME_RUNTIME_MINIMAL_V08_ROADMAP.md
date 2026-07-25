# PATCH_GAME_RUNTIME_MINIMAL_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の**最終到達点候補**。
> ROM + Input + Timer + VRAM を組み合わせ、AKDev 上で「ゲームっぽい最小デモ」が動く土台を作る設計。
> 本書は**設計のみ**。**実装・UI 実装・Game Runtime 実装・VRAM Viewer 実装・CPU 命令追加・ASM 変更・テスト追加・既存挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の Input / ROM / Program Target ROM / AK32 Bitwise / Timer / VRAM device 完了
>（`python -m pytest tests/` → **1164 passed**・VRAM commit `b7b7a35 feat: add vram device`）。

> 位置づけ: **VRAM device の次・`PATCH_V08_STABILIZE_AND_DOCS` の直前**。
> Game Runtime Minimal は新しい CPU 命令や新 runtime class を足さず、**既存の Run/Step に「構成 + サンプル + 表示確認」の薄い層**を重ねるだけにする。

---

## 1. 目的

- ROM / Input / Timer / VRAM を**同時に配置**した最小ゲーム runtime を作る。
- CPU が **ROM からプログラムを fetch して実行**し、**Input を `LD` で読み**、**Timer を `LD` で読み**、**VRAM へ `ST` で描画**する一連の流れを AKDev 上で成立させる。
- VRAM の内容を**最小限の画面表示（32×32 viewer）または dump/viewer** で確認できるようにする。
- v0.8 を閉じる直前の「最小デモ基盤」にする（ゲームっぽい最小デモが Run で動く）。
- **画面表示 panel を今回入れるか、dump/viewer に留めるかを本設計で決める**（→ §4 で決定）。
- **既存 CPU 命令・ASM は原則変更しない**。Game Runtime Minimal は既存命令だけで成立させる。

### スコープ（明確化）

「構成（ROM+Input+Timer+VRAM の demo project / address map）」+「sample program（既存命令のみ）」+「VRAM 表示（最小 32×32 viewer もしくは dump）」+「Step/Run 後の viewer refresh hook」+「最小テスト」。
専用 game runtime class・sprite/tile・palette 本格実装・audio・DMA/GPU・physics・asset system・HDL/FPGA は対象外（§12）。

---

## 2. 現在の到達点（実コード確認）

すべて実装・コミット済み。本パッチはこれらを**組み合わせるだけ**。

- **ROM target 実行**: `set_program_target("rom")` で `reset_pc = rom.base`。`write_program()` が ROM へ image を載せ、ROM から fetch して実行できる（`PATCH_PROGRAM_TARGET_ROM_V08`・`tests/test_vram_device_v08.py::test_rom_target_writes_vram` で実証済み）。
- **Input が MMIO で読める**: `InputPart`（`core/dev.py`）。`+0 KEY_STATE` / `+4 EDGE_STATE`。CPU は既存 `LD` で `bus.read(base)`。UI/テストから `set_keys(mask)`。
- **Timer が MMIO で読める**: `TimerPart`（`core/dev.py`）。`+0 TICK`（monotonic step count）/ `+4 DELTA`。runtime が **1 命令ごとに `tick()`** を呼ぶ deterministic counter。CPU は `LD` で読み、`ST` で clear。
- **VRAM が memory device として読み書き可能**: `VramPart`（`core/dev.py`）。32bit LE word の `read`/`write`（CPU の `LD`/`ST`）＋ 1 byte/pixel の `pixel`/`set_pixel`/`dump`。reset で 0 クリア。indexed color 32×32 / 1 byte/pixel / 1024 B。
- **Run Status に Timer/VRAM が出る**: `_collect_run_status()`（`ui/win.py:962-994`）が `timer`/`vram` dict を渡し、`render_status()`（`ui/run_status.py:77-93`）が `Timer:` / `VRAM:` 行を出す。VRAM 未配置なら `VRAM: None`。
- **既存 Run/Step の流れ**:
  - `MainWin._do_step`（`ui/win.py:1466`）: `_runtime.step()` を 1 回呼び、trace をログ、`_refresh_run_panels()` で全 panel 更新。
  - `MainWin._do_run`（`ui/win.py:1483`）: `_runtime.step()` を最大 1000 回 or halt まで繰り返し、最後に `_refresh_run_panels()`。
  - **`_refresh_run_panels()`（`ui/win.py:1415`）が UART console / register / bus trace / memory viewer / pc highlight / signal overlay / run status を一括更新する一点**。→ **VRAM viewer の refresh はここに 1 行足すだけで載る**。
- **`VirtualCircuitRuntime.step()` の責務**: 1 命令を実行し trace を返す。Timer の `tick()` もここで駆動される（`timer=self._sim_timer` を runtime に渡している・`ui/win.py:371`）。VRAM は通常の bus slave なので runtime は特別扱い不要。
- **`VramPart.dump()` / `pixel()` の現在の使い方**: 今はテスト（`tests/test_vram_device_v08.py`）のみが利用。**UI からはまだ誰も読んでいない**（表示する場所が無い）。

> 結論: 「ゲーム runtime」としてまとめた**起動方法・demo 構成・表示更新単位**がまだ無い。本パッチはその薄い層を足すだけで、`VirtualCircuitRuntime` 本体には触れない。

---

## 3. 最小ゲーム runtime の定義（何をもって完成とするか）

**採用方針: 新 runtime class を足さない。`MainWin` 側に「demo 構成 + sample program + VRAM 表示 + refresh hook」の薄い層を足す。**

完成（Done）の定義:

1. **ROM + Input + Timer + VRAM が同時に配置できる**（demo 構成・game16 layout で overlap 無し）。
2. **ROM target から実行**して、Input 値 / Timer 値 を読み、**Run/Step 後に VRAM 内容が変化する**ことを確認できる。
3. **VRAM 内容を確認できる**（§4 の決定に従い、最小 32×32 viewer もしくは `dump()` ベース）。
4. **viewer を入れる場合、Step/Run/Reset 後に viewer が更新される**（`_refresh_run_panels()` 経由）。
5. **既存の通常 Run/Step（Game 構成でない project）は従来通り**。VRAM 非配置なら viewer は `None`/空表示で無害。

非目標（Done に含めない）:

- 本格的なゲームループ（衝突・スコア・フレーム同期）。
- sprite/tile/palette/audio。
- 専用の `GameRuntime` クラスや独自実行ループ（既存 `_do_run` の 1000 step ループで十分）。

> 推奨どおり: 新 CPU 命令・ASM 変更なし / 既存 `VirtualCircuitRuntime` は壊さない / Game Runtime Minimal は「構成・実行・表示確認」の薄い層 / 表示を入れても 32×32 の最小 viewer に留める。

---

## 4. 画面表示方針（**決定が必要 → 本設計で決定**）

| 案 | 内容 | 長所 | 短所 |
|---|---|---|---|
| A 表示 panel なし | `dump()` + テストのみ | 実装最小 | ゲーム感が弱い |
| **B 最小 VRAM Viewer（採用・第一候補）** | 32×32 の小さい表示 panel・1 byte/pixel を濃淡 or 色で表示・Step/Run 後に更新 | v0.8 の「見た目の到達点」が明確・デモが分かりやすい | UI 追加が要る |
| C Viewer は別パッチ | `PATCH_VRAM_VIEWER_V08` に分離 | Game Runtime の設計に集中できる | v0.8 の見た目成果が遅れる |

**採用: 案 B —「最小 VRAM Viewer を Game Runtime Minimal に含める」。** ただし**明示的なフォールバック条件**を置く（下記）。

- viewer は **単純な 32×32 framebuffer 表示のみ**。sprite/tile/palette は扱わない。
- 1 byte/pixel の値を **グレースケール（0=黒・255=白・中間は濃淡）** で描く。色 palette は後続。
- 描画は **`VramPart.dump()` / `pixel(x,y)` を読むだけ**（VRAM 本体には触れない・別バッファを作らない）。
- 更新は **`_refresh_run_panels()` に viewer refresh を 1 行足す**（Step/Run/Reset/Write の後に自動更新）。
- **VRAM 未配置なら viewer は無効/空表示**（`self._sim_vram is None` の分岐）。既存 project は無害。

> **フォールバック条件（分離判断）**: viewer 実装が「QWidget + paintEvent + dock 配線 + scaling」程度を超えて肥大化する、または既存 UI レイアウト/dock 管理に大きく手を入れる必要が出た場合は、**viewer を `PATCH_VRAM_VIEWER_V08` に切り出し**、本パッチは案 A（構成 + sample + `dump()` テスト）に縮退する。判断は実装着手時の見積りで行い、CHECKLIST に記録する。

---

## 5. Sample Program 方針

最小デモ用 ASM を用意する。**すべて既存命令（`LDI/LD/ST/JMP/BEQ/ADDI/ADD/SUB/AND/OR/XOR/NOT/HALT`）のみ**で書く（opcode 確認: `asm/asm.py:129` = NOP/HALT/LDI/OUT/ADD/SUB/LD/ST/JMP/BEQ/ADDI/AND/OR/XOR/NOT）。

> 注: 下記の MMIO アドレス（Input/Timer）は **layout と配置順で決まる**。game16 では MMIO base=0xE000・stride=0x10 で、配置順に 0xE000 / 0xE010 / 0xE020 … と振られる（`assign_mmio_bases`・`core/devices.py:279`）。**正確な番地は実装時に Address Map / Run Status で確認してからサンプルに焼き込む**こと（下記は VRAM=0xC000 を前提にした雛形）。

### Demo 1: VRAM に固定値を書くだけ（最小確認）

```asm
LDI r1, 0xC000      ; VRAM base
LDI r2, 0x00FF      ; pixel value
ST  [r1], r2        ; VRAM[0] = 0xFF（LE: pixel0=0xFF）
HALT
```

→ Run 後 `dump()[0] == 0xFF` / viewer 左上が白。`test_cpu_writes_and_reads_vram` と同型で実証可能。

### Demo 2: Input で VRAM の値を変える

```asm
LDI r1, 0xE000      ; INPUT KEY_STATE（※実番地は配置順で確認）
LD  r2, [r1]        ; 押下キー bitmask を読む
LDI r3, 0xC000      ; VRAM base
ST  [r3], r2        ; VRAM[0] = キー状態
HALT
```

→ `set_keys(mask)` した状態で Run すると VRAM 先頭に入力が反映される。

### Demo 3: Timer で VRAM の値を変える

```asm
LDI r1, 0xE010      ; TIMER TICK（※実番地は配置順で確認）
LD  r2, [r1]        ; tick を読む
LDI r3, 0xC000      ; VRAM base
ST  [r3], r2        ; VRAM[0] = tick 下位
HALT
```

→ Timer は 1 命令ごとに進むので、HALT 直前の tick が VRAM に入る。

### Demo 4: Run で変化し続ける最小ループ（既存命令で可能か確認）

利用可能: `JMP`(0x08) / `BEQ`(0x09) / `ADDI`(0x0A) / `ST` / `LD` / `ADD` / `SUB`。
不在: **`BNE` なし** / **shift なし** / 比較命令は弱い（`BEQ` のみ）/ **CALL/RET/stack なし**。

雛形（カウンタを VRAM に書き続ける・`JMP` で無限ループ → 1000 step 上限で停止）:

```asm
        LDI r1, 0xC000      ; VRAM base
        LDI r2, 0x0000      ; counter
loop:   ST  [r1], r2        ; VRAM[0] = counter
        ADDI r2, r2, 1      ; counter++
        JMP loop            ; 無限ループ（Run の 1000 step 上限で停止）
```

→ Run（最大 1000 step）後、VRAM 先頭が初期値から変化していることを確認できれば十分。

方針:
- **既存命令だけで可能なデモに限定**。無理に複雑なゲームループを書かない。
- まずは **Run 後に VRAM が変化する**ことを確認できればよい（HALT 版／無限ループ版どちらでも可）。
- `BEQ` で「特定キーが押されたら分岐」程度は可能だが、必須にしない（`AND` でキー bit 抽出 → `BEQ` で 0 判定）。

---

## 6. Memory Layout / Address Map 方針

**採用: `game16` layout を使う**（VRAM フィールドは実装済み = `core/devices.py:75-80`）。

現状の実コード値（確認済み）:

| 領域 | game16 | circuit_compat | legacy |
|---|---|---|---|
| ROM | base=0x0000 / size=0x8000 | rom_base=None | None |
| RAM | base=0x8000 / size=0x4000 | base=0x0000 / size=0x10000（全域） | 0x0000 / 0x0100 |
| VRAM | base=0xC000 / size=0x0400 | None（override 配置） | None |
| MMIO base | 0xE000（stride 0x10） | 0x0100（stride 0x10・RAM 内） | 0x0100 |
| stack_top | 0xBFFF | — | — |
| reset_pc / code_base | 0x0000 | — | — |

- **Input / Timer / UART の MMIO 番地**: `assign_mmio_bases` が running index で `mmio_base + n*stride` を振る（`core/devices.py:300`）。game16 なら 0xE000 / 0xE010 / 0xE020 …。**配置順（spec 順）で決まる**ため、サンプルに焼く前に Address Map で実番地を確認する。
- **game16 では ROM/RAM/VRAM が自動で非重複**: ROM 0x0000–0x7FFF / RAM 0x8000–0xBFFF / VRAM 0xC000–0xC3FF / MMIO 0xE000–。`test_game16_rom_ram_vram_non_overlapping` で実証済み。
- **circuit_compat override 運用も維持**: RAM 全域なので VRAM を 0xC000 に置くには RAM を縮小する manual override が要る（`_vram_override()` = VRAM 0xC000/0x400 + RAM 0x0000/0xC000）。既存テスト互換のため**この経路は壊さない**。
- **`tests/test/system.json` 差分を出さない**: demo 構成は新しい demo project / テスト内構成として持ち、既存の system fixture を書き換えない。

> 推奨どおり: Game Runtime Minimal の標準デモは **game16 layout**（ROM 0x0000 / RAM 0x8000 / VRAM 0xC000 / MMIO 0xE000）。circuit_compat + override の経路も互換維持。

---

## 7. UI 方針

- **VRAM Viewer**（案 B 採用時）:
  - 小さな 32×32 framebuffer 表示 widget（dock もしくは既存 panel 領域に配置）。
  - 拡大表示（1 pixel を数 px の正方形で描く・整数倍スケール）。
  - 色: **最小**。`0=黒・非0=白` もしくは index 値の **グレースケール**。palette は後続。
  - refresh: **`_refresh_run_panels()` に 1 行追加**（Step/Run/Reset/Write 後に自動更新）。
  - VRAM 未配置（`self._sim_vram is None`）なら **空表示 / 無効**。
- **Run Status**: 既に `VRAM: base=.. size=..` / `Timer: tick=.. delta=..` 行がある（`ui/run_status.py`）。**必要なら Game Runtime 用に 1 行追加**（例: demo 名や「Game: ROM+Input+Timer+VRAM」程度）。ただし最小限。Run Status は大改造しない。
- **既存 UI を大きく壊さない**: dock/panel 追加は viewer 1 個に留める。レイアウト管理の大規模変更はしない。

---

## 8. 実装スコープ案（次に実装する場合の安全な範囲）

最小実装範囲（案 B 採用時）:

- **`ui/vram_viewer.py`（新規）**: 32×32 framebuffer を描く widget。入力は `VramPart`（または `dump()` bytes + width/height）。`render(vram)` / `refresh()`。VRAM=None なら空表示。
- **`ui/win.py`**:
  - viewer dock/panel を 1 個生成（`__init__` / `_setup_*`）。
  - `_refresh_run_panels()`（`ui/win.py:1415`）に `self._vram_viewer.render(self._sim_vram)` を 1 行追加。
  - （任意）demo loading helper を足すか検討（ROM+Input+Timer+VRAM をワンタッチ配線する開発用補助）。**必須ではない**・入れるならテスト専用ヘルパー水準に留める。
- **`ui/run_status.py`**: （任意）Game Runtime 欄を 1 行。最小。
- **`tests/test_game_runtime_minimal_v08.py`（新規）**: §10 のテスト。
- **docs 更新**: `PATCH_GAME_RUNTIME_MINIMAL_V08_CHECKLIST.md`・`CHECKLIST8.md`/`ROADMAP8.md` 最小追記・`HANDOFF.md`。

> 案 A（viewer 分離）に縮退する場合: `ui/vram_viewer.py` と viewer 配線を落とし、`dump()` ベースのテスト＋ demo 構成のみにする。

---

## 9. CPU / ASM 方針

- **CPU 命令追加なし**。
- **ASM 変更なし**。
- 既存 `LDI / LD / ST / JMP / BEQ / ADDI / ADD / SUB / AND / OR / XOR / NOT / HALT`（+ `NOP` / `OUT`）の範囲だけで成立させる。
- Branch 拡張（`BNE` / `BEQZ` / `BNEZ`）は**後続** `PATCH_AK32_BRANCH_EXPANSION_V08`。
- Shift / `ANDI` / `ORI` は**後続** `PATCH_AK32_SHIFT_IMM_BITWISE_V08`。
- `CALL` / `RET` / stack は**後続** `PATCH_AK32_STACK_CALL_RET_V08`。
- **Game Runtime Minimal は既存命令で成立させる**（複雑なループは無理に書かない・§5 Demo 4 雛形で十分）。

---

## 10. テスト方針（実装時に追加するテスト）

- ROM + Input + Timer + VRAM が**同時に配置できる**（game16 で 4 device 構成）。
- game16 layout で **overlap しない**（`validate_address_map(amap) == []`）。
- **ROM target から実行して VRAM に書ける**（`test_rom_target_writes_vram` の拡張・Input/Timer も配線した版）。
- **Timer 値を VRAM に書ける**（Demo 3 を Run し、VRAM 先頭が tick 由来の値になる）。
- **Input 値を VRAM に書ける**（`set_keys` 後 Demo 2 を Run し、VRAM 先頭がキー値）。
- **Run 後に VRAM 内容が変わる**（Demo 4 雛形を Run し、初期 0 から変化）。
- viewer を入れるなら: **viewer が `VramPart`/`dump()` を受けて表示状態を更新する**（render 呼び出しで内部状態/pixel 取得が VRAM と一致）。`_refresh_run_panels()` 後に viewer が最新値になる。
- **VRAM 未配置時は既存互換**（viewer 空表示・`self._sim_vram is None`・Hello World が従来通り動く）。
- **Hello World / Input / Timer / VRAM 既存テストが壊れない**。
- `python -m pytest tests/` **全通過**。
- **`tests/test/system.json` 差分なし**。

---

## 11. 既存互換方針（必須）

- 既存 project は壊さない。
- Game Runtime を使わない**通常 Run/Step は従来通り**（`_do_run` / `_do_step` の挙動は変えない・viewer refresh は VRAM 未配置で no-op）。
- **CPU 命令 / ASM は変えない**。
- VRAM Viewer を入れても **VRAM 未配置なら無害**（`self._sim_vram is None` 分岐）。
- **`tests/test/system.json` 差分を出さない**。
- 全 test 通過。

---

## 12. 今回やらないこと

- 実装（コード/UI/Game Runtime/Viewer）
- VRAM Viewer 実装
- Game Runtime 実装
- CPU 命令追加
- ASM 変更
- sprite / tile
- palette 本格実装
- audio
- DMA / GPU
- physics
- game asset system
- HDL / FPGA export
- commit
- push

---

## 13. 次に続くパッチ（候補順）

**最短ルート（v0.8 を閉じる）:**

1. **`PATCH_GAME_RUNTIME_MINIMAL_V08`**（本パッチ — 構成 + sample + 最小 viewer or dump）
2. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

**viewer を分離する場合:**

1. `PATCH_VRAM_VIEWER_V08`（32×32 framebuffer viewer のみ）
2. `PATCH_GAME_RUNTIME_MINIMAL_V08`（構成 + sample・viewer 連携）
3. `PATCH_V08_STABILIZE_AND_DOCS`

**追加で命令拡張するなら（後回し）:**

- `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE` / `BEQZ` / `BNEZ`）
- `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL` / `SHR` / `ANDI` / `ORI`）
- `PATCH_AK32_STACK_CALL_RET_V08`（`CALL` / `RET` / stack）

> **v0.8 を閉じる方針なら、追加命令拡張（Branch/Shift/Stack）は後回し**にする。Game Runtime Minimal は既存命令で成立するので、v0.8 は「VRAM device → Game Runtime Minimal → Stabilize」で閉じ、命令拡張は v0.9 以降に回す。
