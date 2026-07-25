# PATCH_TIMER_DEVICE_V08 — ROADMAP（設計資料）

> v0.8（Device Expansion & Connection Validation）の次パッチ候補。仮想回路上に Timer device を追加する設計。
> 将来の最小ゲーム runtime（時間経過・一定周期処理・ゲームループ・入力更新タイミング）の**最小時間基盤**。
> 本書は設計のみ。**実装・part.json 追加・TimerPart 追加・device registry 変更・CPU 命令追加・ASM 変更・テスト追加・既存挙動変更・commit/push は行わない。**
> 親計画: `ROADMAP8.md` / `CHECKLIST8.md`。所見: `V08_CODEBASE_REVIEW.md`。
> 前提: v0.8 の `PATCH_PORT_SCHEMA_V08` 〜 `PATCH_AK32_BITWISE_INSTRUCTIONS_V08` 完了（`python -m pytest tests/` 1111 passed）。

> **割り込みは扱わない**。Timer は **MMIO device**（CPU 命令追加なし。既存 `LD`/`ST` で読む/clear）。tick は **deterministic（CPU step 数ベース）**。

---

## 1. 目的

- `io.timer` device を追加する（MMIO・UART/Input と同方式）。
- CPU から **既存 `LD`** で現在 tick を読めるようにする。
- CPU から **既存 `ST`** で Timer を clear できるようにする（write の意味は §4 で確定）。
- 将来のゲーム runtime で「一定周期処理」「ゲームループ」「入力更新タイミング」を実現する土台にする。
- Input 更新（`set_input_keys`）や VRAM 描画と組み合わせる時間基盤にする。
- **割り込みは今回扱わない**。**CPU 命令追加なし**。
- **今回は設計のみ**。実装・既存挙動変更はしない。

### スコープ（明確化）

`io.timer` part + `TimerPart`（read/write/reset/tick）+ device registry の runtime 化 + Address Map 統合 + runtime step での tick 進行 + 最小テスト。
割り込み・wall-clock timer・scheduler・VRAM・game runtime・HDL/FPGA は対象外。

---

## 2. 現在の到達点（実コード確認）

- Input device は MMIO で読める（`InputPart`・base 0x0110・既存 `LD`）。ROM target でプログラムを ROM から実行できる。
- Bitwise（`AND`/`OR`/`XOR`/`NOT`）で Input bit 判定ができる。
- **しかし時間経過を CPU program 側で観測する device がまだ無い**。
- **step/cycle の管理場所**:
  - `VirtualCircuitRuntime.step()`（`core/runtime.py`）が `cpu.tick()` を呼び、その後 **`self.step_count += 1`**。
  - `MainWin._do_step` / `_do_run`（`ui/win.py`）は `self._runtime.step()` を回し、**`self._sim_cycle = self._runtime.step_count`** で同期。
  - Run は最大 1000 step、Step は 1 step。Run Status / Register View に **cycle 表示あり**（`self._sim_cycle`）。
  - `Bus(cycle_fn=lambda: self._sim_cycle)`（bus trace 用の cycle 供給）。
- **MMIO device は UART/Input が既に存在**するので、Timer も同方式（`assign_mmio_bases` の running index）に乗せられる。
- **registry は一部すでに Timer 対応済み**（`core/devices.py`）:
  - `_KIND_BY_PART_ID["io.timer"] = "timer"`（**既存**）
  - `_ROLE_BY_KIND["timer"] = "mmio"`（**既存**）→ `is_addressable_kind("timer")` True
  - `_LABEL_BY_KIND["timer"] = "TIMER"`（**既存**）
  - **未対応**: `_RUNTIME_BACKED` に `timer` 無し / `_RUNTIME_ID` に `timer` 無し（→ 現状 runtime 化されない）。
- **MMIO window サイズの重要事実**: `assign_mmio_bases` は **`layout.mmio_size`（=0x08）/ stride 0x10** を全 MMIO に一律適用。
  → Timer の窓も **0x08（2 ワード分）**。UART 0x0100 / Input 0x0110 / Timer **0x0120**（窓 0x0120–0x0127）。

---

## 3. Timer device 仕様案

| 項目 | 値 |
|---|---|
| part_id | `io.timer` |
| name | `Timer` |
| category | `io` |
| kind | `timer`（既存 `_KIND_BY_PART_ID`） |
| role | `mmio`（既存 `_ROLE_BY_KIND`） |
| addressable | true（mmio role） |
| runtime_backed | true（**新規** — `_RUNTIME_BACKED` に追加） |
| runtime_id | `sim_timer`（**新規** — `_RUNTIME_ID` に追加） |
| MMIO window size | **`layout.mmio_size` = 0x08**（UART/Input と同じ。下記注） |
| Address Map 配置 | `assign_mmio_bases` の running index で UART→Input→Timer の順に 0x0100 / 0x0110 / **0x0120** |

> **注（重要・prompt 案の修正）**: prompt は「MMIO window size 0x10」「register 0x00/0x04/0x08/0x0C の 4 本」を例示するが、
> 実コードの `assign_mmio_bases` は **window=0x08（stride 0x10）固定**。窓 0x08 には **2 ワード（0x00 / 0x04）しか入らない**。
> よって本設計は **0x08 窓・2 レジスタの「最小案」（§4）を採用**する。4 レジスタ（TICK_HI/CTRL）は `mmio_size` 拡張が要るため後続。
> base/size の最終確認は実装時に `assign_mmio_bases` で行う（stride 0x10 のため Timer 窓は 0x0120–0x0127）。

---

## 4. Timer MMIO register案（最小案を採用）

**採用案（0x08 窓に収まる 2 レジスタ）**:

| offset | name | read | write | 説明 |
|---:|---|---|---|---|
| `0x00` | `TICK` | 現在 tick（下位 32bit・step 数） | 任意の値の書き込みで **tick を 0 に clear**（値は無視） | 現在 tick |
| `0x04` | `DELTA` | 前回 clear からの経過 tick | 書き込みで **clear（DELTA 基準点を現在 tick に更新）** | 経過 tick |

- `TICK` は **単調増加の step カウンタ**（read）。`ST [0x0120], rx` で **0 に clear**（rx の値は無視＝Input の CLEAR_EDGE と同じ「書けば clear」方式）。
- `DELTA` は `現在 tick - 最後に DELTA を clear した時点の tick`。`ST [0x0124], rx` で基準点を現在 tick に更新。
- read は 32bit LE word（範囲外 offset は 0 を返す＝Input/UART の defensive read 流儀）。
- TICK が 32bit を超えた場合は wrap（`& 0xFFFFFFFF`）。TICK_HI は窓拡張後（後続）。

> **代替（参考・今回不採用）**: 4 レジスタ（TICK_LO/TICK_HI/DELTA/CTRL）は `mmio_size` を 0x10 に広げる必要があり、
> 既存 Address Map（UART/Input の窓計算）に波及するため**今回はやらない**。最小案で時間基盤を成立させる。

---

## 5. tick の単位

- **Timer tick = CPU step 数（`runtime.step_count` と同じ進み方）**。1 CPU 命令実行ごとに +1。
- **wall-clock 時間は使わない**（GUI の実時間と分離）。
- **deterministic**: 同じプログラム・同じ入力なら tick は再現する（テスト容易性最優先）。
- Run（連続実行）でも Step（1 命令）でも、**実行した step 数に応じて増える**。
- GUI の `self._sim_cycle`（=step_count のミラー）とは**別オブジェクト**（Timer は自分の内部カウンタを持つ）。値の意味は一致するが、Timer 未配置でも `_sim_cycle` は従来どおり動く（競合させない）。

---

## 6. runtime 統合方針

- **`TimerPart` を `core/dev.py` に追加**（`tick()` / `reset()` / `read()` / `write()`）。
- **tick を進める場所**: `VirtualCircuitRuntime.step()` が `cpu.tick()` 実行後に `self.step_count += 1` する。**その直後に、timer があれば `self.timer.tick()` を呼ぶ**。
  - runtime は現在 `bus/ram/uart/cpu` を保持。timer は任意なので **`self.timer`（無ければ None）** を持たせ、`if self.timer is not None: self.timer.tick()`。
  - これにより step N の終了時に timer が +1 → step N+1 の `LD` では「それまでに完了した step 数」を読める（deterministic）。
- **reset 連動**:
  - `VirtualCircuitRuntime.reset()`（CPU/UART/trace を reset・RAM は保持）で **timer も reset**（tick=0・DELTA 基準=0）。
  - `load_program`（RAM target）/ ROM target の load 経路でも runtime を作り直す/reset するので **program load 時に timer=0** から始まる。
- **`self._sim_cycle` と競合させない**: timer は独自カウンタ。`_sim_cycle` の更新ロジックは変えない。
- **Timer 未配置なら既存挙動完全互換**（runtime に timer=None → tick 呼び出しなし → 既存と同一）。
- Run / Step どちらでも `runtime.step()` 経由なので **両方で tick が進む**。

> 実装位置の選択肢: (A) `runtime.step()` 内で `self.timer.tick()`（推奨・step と 1:1）。(B) `MainWin._do_step/_do_run` のループで呼ぶ（runtime を汚さないが 2 箇所重複）。**推奨は (A)**。

---

## 7. device registry 方針（`core/devices.py`）

更新候補（**既存で足りているものは確認のみ**）:

- `_KIND_BY_PART_ID["io.timer"] = "timer"`（**既存・確認**）
- `_ROLE_BY_KIND["timer"] = "mmio"`（**既存・確認**）→ addressable True
- `_LABEL_BY_KIND["timer"] = "TIMER"`（**既存・確認**）
- `_RUNTIME_BACKED` に `"timer"` を追加（**新規**）→ `is_runtime_backed_kind("timer")` True
- `_RUNTIME_ID["timer"] = "sim_timer"`（**新規**）
- `_base_size`: timer は mmio role なので **`assign_mmio_bases` が base/size を付与**（`_base_size` の分岐追加は不要。UART 以外の mmio は `assign_mmio_bases` 任せ＝Input と同じ）。
- `make_device_spec()` が Timer spec を作れる（role mmio・addressable・runtime_backed・runtime_id sim_timer・base/size は `assign_mmio_bases` で確定）。
- **複数 Timer 時**: `assign_mmio_bases` の per-kind ロジックで **1 個目だけ runtime-backed**（2 個目以降は placement-only・`runtime_id=None`）。UART2/Input2 と同じ扱い。
  - `multi_device_warnings` は現状 RAM のみ警告。Timer は per-kind ロジックで自然に処理されるため**追加警告は任意**（必要なら拡張）。

---

## 8. part.json 方針

`parts/io/timer/part.json`（**新規**・schema v2・`io.input` / `io.uart` と同形）:

```json
{
  "id": "io.timer",
  "name": "Timer",
  "category": "io",
  "schema_version": 2,
  "ports": [
    {"name": "bus",   "type": "bus.slave", "role": "slave", "direction": "inout", "width": 32, "required": true,  "description": "Register bus (slave)"},
    {"name": "clk",   "type": "clock",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Clock input"},
    {"name": "reset", "type": "reset",     "role": null,    "direction": "in",    "width": 1,  "required": true,  "description": "Reset input"}
  ]
}
```

- id `io.timer` / name `Timer` / category `io` / `schema_version: 2`。
- ports: `bus`(bus.slave) + `clk` + `reset`（Input の `keys` のような専用入力は不要＝tick は内部 step 由来）。
- visual / icon は既存 io 系のカテゴリ色を流用。

---

## 9. resolve_circuit 方針（`core/circuit.py`）

- 便宜キー **`plan["timers"]`** を追加（`rams`/`uarts`/`inputs`/`roms` と同形・target CPU に wired な timer node・sort 済み）。
- `plan["devices"]`（addressable 全 kind）には timer も含まれる（mmio role なので既存収集に乗る）。
- 既存キー（`cpu / rams / uarts / inputs / roms / devices / target_cpu / cpu_present / ok / issues`）は**互換維持**。
- target CPU と wired な Timer のみ収集（bus 未接続 Timer は収集しない＝Address Map に出さない）。
- **Timer が無くても `ok` 判定は変えない**（Timer は必須にしない）。
- **Timer があっても RAM/ROM/Input を必須にしない**。

---

## 10. UI / Run Status 方針

- **Address Map に Timer 行が出る**（base 0x0120・size 0x08）。
- **Address Map Editor で base/size override 可**（既存 `apply_address_overrides` / `validate_address_overrides`）。
- **Run Status に `Timer: tick=...` を追加できるなら追加**（`_collect_run_status` に `timer_tick` を入れ、`run_status.py:render_status` に 1 行）。Program Target 行を足したのと同じ最小パターン。Timer 未配置なら `Timer: (none)`。
- Port Detail で timer の port が見える（既存 port detail に自動で乗る）。
- Log に Timer 配置情報（Address Map summary）が出る（既存 `_log_address_map`）。
- **UI 大改造はしない**。最小実装は Address Map 表示 + tests 優先。GUI 目視はヘッドレスのため未実施になる可能性あり（その旨記録）。

---

## 11. CPU / ASM との関係

- Timer は **MMIO device なので CPU 命令追加は不要**。
- **既存 `LD rd, [rs]`** で Timer を読む（`rs` に 0x0120 を入れて TICK、0x0124 で DELTA）。
- **既存 `ST [rd], rs`** で Timer を clear（TICK/DELTA を 0/基準更新）。
- **`IN` 命令は不要**（Input と同じく MMIO read）。
- Bitwise 命令は Timer 自体には必須ではない（tick 値のマスク等で使える程度）。
- 将来、**Input + Timer + VRAM** でゲームループを作る（`PATCH_GAME_RUNTIME_MINIMAL_V08`）。

---

## 12. サンプル ASM 方針

現在は比較命令が弱い（`BEQ` 等値のみ・`BNE`/`BLT` 未実装）ため、**まずは読み取り確認に留める**:

```asm
    LDI r1, 0x0120     # Timer TICK base（Address Map に合わせる）
    LD  r2, [r1]       # 現在 tick を r2 へ
    HALT
```

clear の確認:

```asm
    LDI r1, 0x0120
    ST  [r1], r0       # tick を clear（r0=0 を書く＝値は無視され clear）
    LD  r2, [r1]       # clear 直後の tick を読む
    HALT
```

> 「tick==N で分岐」のループ的サンプルは `BEQ` で書けるが脆い（タイミング依存）。本パッチでは read/clear の確認サンプルに留め、
> ループ的活用は branch 拡張（`PATCH_AK32_BRANCH_EXPANSION_V08`）/ game runtime 側で扱う。

---

## 13. テスト方針（実装時に追加するテスト）

- `io.timer` が Library に出る・v2 schema 正規化。
- `device_kind({"id":"io.timer"}) == "timer"` / `device_role("timer") == "mmio"` / addressable・runtime_backed・runtime_id sim_timer。
- `make_device_spec` が Timer spec を作る。
- Timer が Address Map に載る（base 0x0120・size 0x08）。
- **UART+Input+Timer で base が 0x0100 / 0x0110 / 0x0120**。
- **Timer 無し構成は既存 Address Map dict 完全一致**。
- `TimerPart`: `read()`（TICK/DELTA）・`write()`（clear）・`reset()`・`tick()`（+1）。
- **Timer tick が CPU step で増える**（`runtime.step()` を N 回 → TICK==N）。
- **Program reload / reset で Timer が reset**（tick=0）。
- **CPU から `LD` で Timer tick を読める**（MainWin 統合・`LD [0x0120]`）。
- **CPU から `ST` で Timer clear できる**（`ST [0x0120]` 後に TICK が小さくなる）。
- 複数 Timer は 1 個目のみ runtime-backed（2 個目は placement-only）。
- **Timer 未配置時は既存挙動完全互換**。
- Hello World / ram_selftest / Input / ROM / Program Target / Bitwise 既存テストが壊れない。
- `python -m pytest tests/` 全通過。

---

## 14. 既存互換方針（必須）

- **Timer を置かない既存 project は完全互換**（runtime に timer=None・tick 呼び出しなし）。
- 既存 Address Map は変えない（Timer 非配置なら dict 一致）。
- 既存 CPU 命令・既存 ASM は変えない。
- Hello World / ram_selftest を壊さない。
- Input / ROM / Program Target / Bitwise テストを壊さない。
- `tests/test/system.json` に差分を出さない。
- `python -m pytest tests/` 全通過。

---

## 15. 実装スコープ案（次に実装するなら・安全な範囲）

- `parts/io/timer/part.json` 追加（v2）。
- `core/devices.py`: `_RUNTIME_BACKED` に `timer` / `_RUNTIME_ID["timer"]="sim_timer"`（kind/role/label は既存・確認のみ）。
- `core/dev.py`: `TimerPart`（`tick()` で内部カウンタ +1・`read` TICK/DELTA・`write` clear・`reset`）。
- `core/circuit.py:resolve_circuit`: `plan["timers"]` 追加（devices は既に収集）。
- `core/runtime.py`: `VirtualCircuitRuntime` に `timer`（任意）保持 + `step()` の step_count++ 後に `timer.tick()` + `reset()` で timer reset。
- `ui/win.py`: `_auto_device_specs` が Timer も spec 化、`_build_runtime_devices` が 1 個目 Timer を runtime 化（`self._sim_timer` / `self._sim_timer_node`・parts_by_id に sim_timer・runtime に timer を渡す）。
- `ui/run_status.py`: 可能なら `Timer: tick=...` 表示。
- tests 追加: `tests/test_timer_device_v08.py`。
- `PATCH_TIMER_DEVICE_V08_CHECKLIST.md` 更新・`CHECKLIST8.md` / `ROADMAP8.md` 最小追記。
- **既定（Timer 非配置）は現行互換**。

やらないこと: 割り込み・wall-clock・scheduler・4 レジスタ化（mmio_size 拡張）・VRAM・game runtime・CPU 命令追加。

---

## 16. 今回やらないこと

- 実装 / `parts/io/timer/part.json` 追加 / `TimerPart` 追加 / device registry 変更
- CPU 命令追加 / ASM 変更 / tests 追加
- 割り込み（interrupt）
- real-time / wall-clock timer
- scheduler
- VRAM 実装
- Game Runtime 実装
- HDL / FPGA export
- 既存挙動変更 / commit / push

---

## 17. 次に続くパッチ（候補順）

1. **`PATCH_TIMER_DEVICE_V08`（本パッチ — MMIO Timer・deterministic tick・割り込みなし）**
2. `PATCH_VRAM_DEVICE_V08`（VRAM device・簡易描画の受け皿）
3. `PATCH_GAME_RUNTIME_MINIMAL_V08`（ROM + Input + Timer + VRAM の最小ゲームループ）
4. `PATCH_AK32_SHIFT_IMM_BITWISE_V08`（`SHL`/`SHR`/`ANDI`/`ORI`）
5. `PATCH_AK32_BRANCH_EXPANSION_V08`（`BNE`/`BEQZ`/`BNEZ` — Timer ループ判定に効く）
6. `PATCH_AK32_STACK_CALL_RET_V08`（`PUSH`/`POP`/`CALL`/`RET` + stack）
7. `PATCH_V08_STABILIZE_AND_DOCS`（v0.8 安定化・ドキュメント・PHASE COMPLETE 準備）

> **v0.8 完了を急ぐ場合は Timer → VRAM → Game Runtime Minimal → Stabilize の順を推奨**。
> ISA 拡張（shift/branch/stack）はゲームループを豊かにするが、最小ループ成立には Timer/VRAM の方が先。
> 横断候補（`V08_CODEBASE_REVIEW.md` §4）: opcode 単一化 / Diagnostics Panel / テストフィクスチャ整理。
